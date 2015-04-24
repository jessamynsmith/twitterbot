import logging

from twitter import Twitter, TwitterHTTPError
from twitter.oauth import OAuth

from .settings import SettingsError


logging.basicConfig(filename='logs/twitter_bot.log',
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    level=logging.DEBUG)


def get_class(class_or_name):
    if isinstance(class_or_name, str):
        class_or_name = _get_class_by_name(class_or_name)
    return class_or_name()


def _get_class_by_name(class_name):
    module_name, symbol_name = class_name.rsplit('.', 1)
    module = __import__(module_name, fromlist=symbol_name)
    return getattr(module, symbol_name)


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
                                "'messages.HelloWorldMessageProvider' will be used.")
                raise SettingsError(message.format(*format_args))

    def __init__(self, settings):
        """ Create a TwitterBot based on settings
        :param settings: settings module
        :return: Instantiated TwitterBot
        """
        self.MESSAGE_LENGTH = 140
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
        self.since_id = get_class(settings.SINCE_ID_PROVIDER)
        self.dry_run = settings.DRY_RUN

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
        mention_length = 0
        if mentions:
            mention_text = " ".join(mentions)
            message = '{0} {1}'.format(mention_text, message)
            mention_length = len(mention_text) + 1
        if len(message) <= max_length:
            return [message]

        tokens = message.split(' ')
        indices = []
        index = 1
        length = len(tokens[0])
        while index < len(tokens):
            # 1 for leading space, 4 for trailing " ..."
            if length + 1 + len(tokens[index]) + 4 > max_length:
                indices.append(index)
                # 4 for leading "... "
                length = 4 + mention_length + len(tokens[index])
            else:
                # 1 for leading space
                length += 1 + len(tokens[index])
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
        messages = self.tokenize(message, self.MESSAGE_LENGTH, mentions)
        code = 0
        for message in messages:
            if self.dry_run:
                mention_message = ''
                if mention_id:
                    mention_message = " to mention_id '{0}'".format(mention_id)
                logging.info("Not posting to Twitter because DRY_RUN is set. Would have posted "
                             "the following message{0}:\n{1}".format(mention_message, message))
            else:
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
        since_id = self.since_id.get()

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
                if name != mention['in_reply_to_screen_name']:
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
                    # Tried 10 times to post a message, but all were duplicates
                    message = 'No unique messages found.'
                else:
                    message = self.messages.create(mention, self.MESSAGE_LENGTH)
                error_code = self.send_message(message, mention_id, mentions)
                tries += 1

            mentions_processed += 1
            self.since_id.set('{0}'.format(mention_id))

        return mentions_processed

    def post_message(self):
        """
        Creates a message with the message provider and posts it to twitter
        :return: Status code from twitter (0 on success)
        """
        return self.send_message(self.messages.create({}, self.MESSAGE_LENGTH))


class BotRunner(object):
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


__all__ = ["BotRunner", "TwitterBot"]
