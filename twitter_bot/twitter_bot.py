import logging
import os

from twitter import Twitter, TwitterHTTPError
from twitter.oauth import OAuth


logging.basicConfig(filename='logs/twitter_bot.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    level=logging.DEBUG)


class Settings(object):
    """ Settings for TwitterBot
    You can use Settings as-is by setting environment variables, or subclass
    Settings to override values
    """
    def __init__(self):
        # Twitter settings (create a twitter account with oauth enabled to get values)
        self.OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        self.OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        self.CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        self.CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

        # Filename to be used to store since_id. This is used when retrieving mentions;
        # only new mentions since since_id will be retrieved. If no value is specified,
        # ALL available mentions will be retrieved
        filename = os.environ.get('TWITTER_SINCE_ID_FILENAME', '.since_id.txt')
        self.SINCE_ID_FILENAME = os.path.join(os.getcwd(), filename)

        # Messages provider
        self.MESSAGE_PROVIDER = os.environ.get('TWITTER_MESSAGE_PROVIDER',
                                               'messages.HelloWorldMessageProvider')


def get_class(module_name):
    module_parts = module_name.split('.')
    module = __import__('.'.join(module_parts[:-1]), fromlist=(module_parts[-1],))
    class_ = getattr(module, module_parts[-1])
    return class_()


class SettingsError(Exception):
    pass


class TwitterBot(object):
    """ Bot for interacting with Twitter
    Can reply to mentions and post new messages
    """

    def _verify_settings(self, settings, required_list, message, count=2):
        for required in required_list:
            if not settings.__dict__.get(required):
                format_args = [required] * count
                if required == 'MESSAGE_PROVIDER':
                    message += (" If TWITTER_MESSAGE_PROVIDER is not set, "
                                "'messages.HelloWorldMessageProvider' will be used")
                raise SettingsError(message.format(*format_args))

    def __init__(self, settings):
        """ Create a TwitterBot based on settings
        :param settings: settings module
        :return: Instantiated TwitterBot
        """

        self.DUPLICATE_CODE = 187

        required_twitter_settings = ('OAUTH_TOKEN', 'OAUTH_SECRET',
                                     'CONSUMER_KEY', 'CONSUMER_SECRET',
                                     'MESSAGE_PROVIDER')
        message = ("Must specify '{0}' in settings.py. When using default settings, "
                   "this value is loaded from the TWITTER_{1} environment variable.")
        self._verify_settings(settings, required_twitter_settings, message)

        auth = OAuth(
            settings.OAUTH_TOKEN,
            settings.OAUTH_SECRET,
            settings.CONSUMER_KEY,
            settings.CONSUMER_SECRET
        )
        self.twitter = Twitter(auth=auth)

        self.messages = get_class(settings.MESSAGE_PROVIDER)
        self.since_id_filename = settings.SINCE_ID_FILENAME

    def _get_since_id(self):
        since_id = ''
        try:
            with open(self.since_id_filename) as since_id_file:
                since_id = since_id_file.readline()
        except IOError:
            pass
        logging.info("Retrieved since_id: %s" % since_id)
        return since_id

    def _set_since_id(self, since_id):
        temp_filename = '{0}.tmp'.format(self.since_id_filename)
        with open(temp_filename, 'w') as since_id_file:
            since_id_file.write(since_id)
        os.rename(temp_filename, self.since_id_filename)
        logging.info("Stored since_id: %s" % since_id)

    def _get_error(self, base_message, hashtags=tuple()):
        message = base_message
        if len(hashtags) > 0:
            hashed_tags = ['#{0}'.format(x) for x in hashtags]
            hash_message = " ".join(hashed_tags)
            message = '{0} matching {1}'.format(base_message, hash_message)
        return message

    def tokenize(self, message, max_length, mentions=None):
        """
        Tokenize a message into a list of messages of no more than max_length, including mentions
        in each message
        :param message: Message to be sent
        :param max_length: Maximum allowed length for each resulting message
        :param mentions: List of usernames to mention in each message
        :return:
        """
        mention_text = ''
        if mentions:
            mention_text = " ".join(mentions)
            message = '{0} {1}'.format(mention_text, message)
        if len(message) < max_length:
            return [message]

        # -4 for trailing ' ...'
        max_length = max_length - 4
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
        """
        Send the specified message to twitter, with appropriate mentions, tokenized as necessary
        :param message: Message to be sent
        :param mention_id: In-reply-to mention_id (to link messages to a previous message)
        :param mentions: List of usernames to mention in reply
        :return:
        """
        messages = self.tokenize(message, 140, mentions)
        code = 0
        for message in messages:
            try:
                self.twitter.statuses.update(status=message,
                                             in_reply_to_status_id=mention_id)
            except TwitterHTTPError as e:
                logging.error('Unable to post to twitter: {0}'.format(e))
                code = e.response_data['errors'][0]['code']
        return code

    def reply_to_mentions(self):
        """
        For every mention since since_id, create a message with the provider and use it to
        reply to the mention
        :return: Number of mentions processed
        """
        since_id = self._get_since_id()

        kwargs = {'count': 200}
        if since_id:
            kwargs['since_id'] = since_id

        mentions_list = []
        try:
            mentions_list = self.twitter.statuses.mentions_timeline(**kwargs)
        except TwitterHTTPError as e:
            logging.error('Unable to retrieve mentions from twitter: {0}'.format(e))

        logging.info("Retrieved {0} mentions".format(len(mentions_list)))

        mentions_processed = 0
        # We want to process least recent to most recent, so that since_id is set properly
        for mention in reversed(mentions_list):
            mention_id = mention['id']

            # Allow users to tweet messages at other users, but don't include self
            mentions = set()
            mentions.add('@{0}'.format(mention['user']['screen_name']))
            for user in mention['entities']['user_mentions']:
                name = user['screen_name']
                if name != 'heartbotapp':
                    mentions.add('@{0}'.format(name))
            mentions = sorted(list(mentions))

            error_code = self.DUPLICATE_CODE
            tries = 0
            message = ''
            while error_code == self.DUPLICATE_CODE:
                if tries > 10:
                    logging.error('Unable to post duplicate message to {0}: {1}'.format(
                                  mentions, message))
                    break
                elif tries == 10:
                    message = self._get_error('No messages found.')
                else:
                    message = self.messages.create()
                error_code = self.send_message(message, mention_id, mentions)
                tries += 1

            mentions_processed += 1
            self._set_since_id('{0}'.format(mention_id))

        return mentions_processed

    def post_message(self):
        """
        Creates a message with the message provider and posts it to twitter
        :return: Status code from twitter (0 on success)
        """
        return self.send_message(self.messages.create())


class Runner(object):
    """ Wrapper for running TwitterBot
    """
    def go(self, settings, command):
        """
        Run the specified command using a TwitterBot created with the provided settings
        :param settings: Settings class
        :param command: Command to run, either 'post_message' or 'reply_to_mentions'
        :return: Result of running the command
        """
        bot = TwitterBot(settings)

        result = 1
        if command == 'post_message':
            result = bot.post_message()
        elif command == 'reply_to_mentions':
            result = bot.reply_to_mentions()
        else:
            print("Command must be either 'post_message' or 'reply_to_mentions'")

        return result
