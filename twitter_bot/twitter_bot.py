import logging
import os

import pymongo
from twitter import Twitter
from twitter.oauth import OAuth
from twitter.api import TwitterHTTPError

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)


class Settings(object):
    """ Settings for TwitterBot """
    def __init__(self):
        # Twitter settings (create a twitter account with oauth enabled to get values)
        self.OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        self.OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        self.CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        self.CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

        # Mongo URI, local or remote
        self.MONGO_URI = 'mongodb://127.0.0.1/local'

        # Messages provider
        self.MESSAGES_PROVIDER = 'messages.HelloWorldMessageProvider'


def get_class(module_name):
    module_parts = module_name.split('.')
    module = __import__('.'.join(module_parts[:-1]), fromlist=(module_parts[-1],))
    class_ = getattr(module, module_parts[-1])
    return class_()


def get_mongo(mongo_uri):
    """ Get mongo database instance based on uri
    :param mongo_uri: connection string uri for mongo
    :return: mongo instance, with database selected
    """
    mongo = pymongo.MongoClient(mongo_uri)
    if mongo:
        config = pymongo.uri_parser.parse_uri(mongo_uri)
        return mongo[config['database']]
    return None


class SettingsError(Exception):
    pass


class TwitterBot(object):

    def _verify_settings(self, settings, required_list, message, count):
        for required in required_list:
            if not settings.__dict__.get(required):
                format_args = [required] * count
                raise SettingsError(message.format(*format_args))

    def __init__(self, settings):
        """ Create a TwitterBot based on settings
        :param settings: settings module
        :return: Instantiated TwitterBot
        """

        self.DUPLICATE_CODE = 187

        required_twitter_settings = ('OAUTH_TOKEN', 'OAUTH_SECRET',
                                     'CONSUMER_KEY', 'CONSUMER_SECRET')
        message = ("Must specify '{0}' in settings.py. When using default settings, "
                   "this value is loaded from the TWITTER_{1} environment variable.")
        self._verify_settings(settings, required_twitter_settings, message, 2)
        self._verify_settings(settings, ('MONGO_URI', 'MESSAGES_PROVIDER'),
                              "Must specify '{0}' in settings.py.", 1)

        auth = OAuth(
            settings.OAUTH_TOKEN,
            settings.OAUTH_SECRET,
            settings.CONSUMER_KEY,
            settings.CONSUMER_SECRET
        )
        self.twitter = Twitter(auth=auth)

        self.messages = get_class(settings.MESSAGES_PROVIDER)

        self.mongo = get_mongo(settings.MONGO_URI)

    def get_error(self, base_message, hashtags=tuple()):
        message = base_message
        if len(hashtags) > 0:
            hashed_tags = ['#%s' % x for x in hashtags]
            hash_message = " ".join(hashed_tags)
            message = '%s matching %s' % (base_message, hash_message)
        return message

    def tokenize(self, message, message_length, mentions=None):
        mention_text = ''
        if mentions:
            mention_text = " ".join(mentions)
            message = '%s %s' % (mention_text, message)
        if len(message) < message_length:
            return [message]

        # -4 for trailing ' ...'
        max_length = message_length - 4
        if mentions:
            # adjust for prepending mentions to each message
            max_length -= len(mention_text)
        tokens = message.split(' ')
        indices = []
        index = 1
        length = len(tokens[0])
        for i in range(1, len(tokens)):
            if length + 1 + len(tokens[i]) >= max_length:
                indices.append(index)
                # 3 for leading "..."
                length = 3 + len(mention_text) + len(tokens[i])
            else:
                length += 1 + len(tokens[i])
            index += 1

        indices.append(index)

        messages = [" ".join(tokens[0:indices[0]])]
        for i in range(1, len(indices)):
            messages[i-1] += ' ...'
            parts = []
            if mention_text:
                parts.append(mention_text)
            parts.append("...")
            parts.extend(tokens[indices[i-1]:indices[i]])
            messages.append(" ".join(parts))

        return messages

    def send_message(self, message, mention_id=None, mentions=[]):
        messages = self.tokenize(message, 140, mentions)
        code = 0
        for message in messages:
            try:
                self.twitter.statuses.update(status=message,
                                             in_reply_to_status_id=mention_id)
            except TwitterHTTPError as e:
                logging.error('Unable to post to twitter: %s' % e)
                code = e.response_data['errors'][0]['code']
        return code

    def reply_to_mentions(self):
        since_id = self.mongo.since_id.find_one()
        logging.debug("Retrieved since_id: %s" % since_id)

        kwargs = {'count': 200}
        if since_id:
            kwargs['since_id'] = since_id['id']

        mentions_list = self.twitter.statuses.mentions_timeline(**kwargs)
        logging.info("Retrieved %s mentions" % len(mentions_list))

        mentions_processed = 0
        # We want to process least recent to most recent, so that since_id is set properly
        for mention in reversed(mentions_list):
            mention_id = mention['id']

            # Allow users to tweet messages at other users, but don't include self
            mentions = set()
            mentions.add('@%s' % mention['user']['screen_name'])
            for user in mention['entities']['user_mentions']:
                name = user['screen_name']
                if name != 'heartbotapp':
                    mentions.add('@%s' % name)
            mentions = sorted(list(mentions))

            error_code = self.DUPLICATE_CODE
            tries = 0
            message = ''
            while error_code == self.DUPLICATE_CODE:
                if tries > 10:
                    logging.error('Unable to post duplicate message to %s: %s'
                                  % (mentions, message))
                    break
                elif tries == 10:
                    message = self.get_error('No messages found.')
                else:
                    message = self.messages.create()
                error_code = self.send_message(message, mention_id, mentions)
                tries += 1

            mentions_processed += 1
            logging.info("Attempting to store since_id: %s" % mention_id)
            self.mongo.since_id.delete_many({})
            self.mongo.since_id.insert_one({'id': mention_id})

        return mentions_processed

    def post_message(self):
        return self.send_message(self.messages.create())


class Runner(object):
    def go(self, settings_module, command):
        bot = TwitterBot(settings_module)

        result = 1
        if command == 'post_message':
            result = bot.post_message()
        elif command == 'reply_to_mentions':
            result = bot.reply_to_mentions()
        else:
            print("Command must be either 'post_message' or 'reply_to_mentions'")

        return result
