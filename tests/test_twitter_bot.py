import os
import unittest
from mock import call, MagicMock, patch
from twitter.api import TwitterHTTPError

from twitter_bot.settings import Settings, SettingsError
from twitter_bot.twitter_bot import BotRunner, get_class, TwitterBot
import twitter_bot.messages
import twitter_bot.since_id


class MockSettings(Settings):
    """ Test settings """
    def __init__(self):
        super(MockSettings, self).__init__()
        self.OAUTH_TOKEN = 'change_me'
        self.OAUTH_SECRET = 'change_me'
        self.CONSUMER_KEY = 'change_me'
        self.CONSUMER_SECRET = 'change_me'
        self.MESSAGE_PROVIDER = 'twitter_bot.messages.HelloWorldMessageProvider'
        self.SINCE_ID_PROVIDER = 'twitter_bot.since_id.FileSystemProvider'
        self.DRY_RUN = False


class MockSymbolicSettings(Settings):
    """ Test settings """
    def __init__(self):
        super(MockSymbolicSettings, self).__init__()
        self.OAUTH_TOKEN = 'change_me'
        self.OAUTH_SECRET = 'change_me'
        self.CONSUMER_KEY = 'change_me'
        self.CONSUMER_SECRET = 'change_me'
        self.MESSAGE_PROVIDER = twitter_bot.messages.HelloWorldMessageProvider
        self.SINCE_ID_PROVIDER = twitter_bot.since_id.FileSystemProvider
        self.DRY_RUN = False


class MockTwitterHTTPError(TwitterHTTPError):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return '{0}'.format(self.e)


class TestGetClass(unittest.TestCase):

    def test_get_class_string(self):
        class_ = get_class('tests.test_twitter_bot.MockSymbolicSettings')

        self.assertTrue(isinstance(class_, MockSymbolicSettings))

    def test_get_class_class(self):
        class_ = get_class(MockSymbolicSettings)

        self.assertTrue(isinstance(class_, MockSymbolicSettings))


class TestTwitterBot(unittest.TestCase):
    MESSAGE = "You don't manage people, you manage things. You lead people. - Grace Hopper"

    def setUp(self):
        self.maxDiff = None
        self.bot = TwitterBot(MockSettings())

    def test_constructor_invalid_settings(self):
        invalid_settings = MockSettings()
        invalid_settings.OAUTH_SECRET = None

        try:
            TwitterBot(settings=invalid_settings)
            self.fail("Shouldn't be able to create TwitterBot with missing setting")
        except SettingsError as e:
            self.assertEqual("Must specify 'OAUTH_SECRET' in settings.py. When using default "
                             "settings, this value is loaded from the TWITTER_OAUTH_SECRET "
                             "environment variable.", '{0}'.format(e))

    def test_constructor_invalid_settings_message_provider(self):
        invalid_settings = MockSettings()
        invalid_settings.MESSAGE_PROVIDER = None

        try:
            TwitterBot(settings=invalid_settings)
            self.fail("Shouldn't be able to create TwitterBot with missing setting")
        except SettingsError as e:
            self.assertEqual("Must specify 'MESSAGE_PROVIDER' in settings.py. When using default "
                             "settings, this value is loaded from the TWITTER_MESSAGE_PROVIDER "
                             "environment variable. If TWITTER_MESSAGE_PROVIDER is not set, "
                             "'messages.HelloWorldMessageProvider' will be used.", '{0}'.format(e))

    def test_constructor_symbolic_config(self):
        settings = MockSymbolicSettings()

        bot = TwitterBot(settings=settings)
        # assertIsInstance came in in python 2.7; this lib supports 2.6.
        self.assertTrue(isinstance(bot.messages, twitter_bot.messages.HelloWorldMessageProvider))
        self.assertTrue(isinstance(bot.since_id, twitter_bot.since_id.FileSystemProvider))

    def test_tokenize_short(self):
        messages = self.bot.tokenize(self.MESSAGE, 80)

        self.assertEqual(1, len(messages))
        self.assertEqual(self.MESSAGE, messages[0])

    def test_tokenize_too_long(self):
        messages = self.bot.tokenize(self.MESSAGE, 50)

        self.assertEqual(2, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 50)
        self.assertEqual("You don't manage people, you manage things. ...", messages[0])
        self.assertEqual("... You lead people. - Grace Hopper", messages[1])

    def test_tokenize_much_too_long(self):
        messages = self.bot.tokenize(self.MESSAGE, 30)

        self.assertEqual(4, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 30)
        self.assertEqual("You don't manage people, ...", messages[0])
        self.assertEqual("... you manage things. You ...", messages[1])
        self.assertEqual("... lead people. - Grace ...", messages[2])
        self.assertEqual("... Hopper", messages[3])

    def test_tokenize_short_with_mention(self):
        messages = self.bot.tokenize(self.MESSAGE, 80, ['@js'])

        self.assertEqual(1, len(messages))
        self.assertEqual('@js {0}'.format(self.MESSAGE), messages[0])

    def test_tokenize_much_too_long_with_mention(self):
        messages = self.bot.tokenize(self.MESSAGE, 40, ['@js'])

        self.assertEqual(3, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 40)
        self.assertEqual("@js You don't manage people, you ...", messages[0])
        self.assertEqual("@js ... manage things. You lead ...", messages[1])
        self.assertEqual("@js ... people. - Grace Hopper", messages[2])

    def test_send_message_dry_run_no_mention(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses
        self.bot.dry_run = True

        result = self.bot.send_message('You are a bright light.')

        self.assertEqual(0, result)
        self.assertEqual(0, mock_statuses.update.call_count)

    def test_send_message_dry_run_with_mention_id(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses
        self.bot.dry_run = True

        result = self.bot.send_message('You are a bright light.', mention_id='12345')

        self.assertEqual(0, result)
        self.assertEqual(0, mock_statuses.update.call_count)

    def test_send_message_no_mention(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.send_message('You are a bright light.')

        self.assertEqual(0, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=None)

    def test_send_message_with_mention(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.send_message('You are a bright light.', mention_id=2)

        self.assertEqual(0, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=2)

    def test_send_message_unknown_error(self):
        error = TwitterHTTPError(
            MagicMock(headers={'Content-Encoding': ''}), '', '', [])
        error.response_data = {"errors": [{"code": 187}]}
        mock_update = MagicMock(side_effect=error)
        mock_statuses = MagicMock()
        mock_statuses.update = mock_update
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.send_message('You are a bright light.')

        self.assertEqual(187, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=None)


class TestReplyToMentions(unittest.TestCase):
    def setUp(self):
        self.bot = TwitterBot(MockSettings())
        self.bot.twitter.statuses = MagicMock()
        self.bot.send_message = MagicMock()
        self.bot.since_id.delete()

    def tearDown(self):
        if os.path.exists(self.bot.since_id.filename):
            os.remove(self.bot.since_id.filename)

    def test_reply_to_mentions_retrieve_error(self):
        self.bot.twitter.statuses.mentions_timeline.side_effect = MockTwitterHTTPError('Fail!')

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(count=200)

    def test_reply_to_mentions_no_mentions_no_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(count=200)

    def test_reply_to_mentions_no_mentions_with_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []
        self.bot.since_id.set('3')

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(count=200, since_id='3')
        self.assertEqual([], self.bot.send_message.mock_calls)

    def test_reply_to_mentions_post_error(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'user_mentions': []}}
        ]
        self.bot.send_message.return_value = 187

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with(count=200)
        self.assertEqual(11, len(self.bot.send_message.mock_calls))
        expected_call = call('Hello World!', '123', ['@jessamyn'])
        self.assertEqual(expected_call, self.bot.send_message.mock_calls[0])
        expected_call = call('No unique messages found.', '123', ['@jessamyn'])
        self.assertEqual(expected_call, self.bot.send_message.mock_calls[10])

    def test_reply_to_mentions_success(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'in_reply_to_screen_name': 'somebot',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'user_mentions': [{'screen_name': 'somebot'},
                                            {'screen_name': 'jill'}]}}
        ]
        self.bot.send_message.return_value = 0

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with(count=200)
        expected_calls = [call('Hello World!', '123', ['@jessamyn', '@jill'])]
        self.assertEqual(expected_calls, self.bot.send_message.mock_calls)

    def test_post_message(self):
        self.bot.send_message.return_value = 0

        result = self.bot.post_message()

        self.assertEqual(0, result)
        self.bot.send_message.assert_called_once_with("Hello World!")


class TestBotRunner(unittest.TestCase):
    def setUp(self):
        self.settings = MockSettings()
        self.runner = BotRunner()

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    def test_go_invalid_arg(self, mock_post):
        mock_post.return_value = 33

        result = self.runner.go(self.settings, 'bogus')

        self.assertEqual(1, result)
        self.assertEqual(0, mock_post.call_count)

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    def test_go_post_message(self, mock_post):
        mock_post.return_value = 33

        result = self.runner.go(self.settings, 'post_message')

        self.assertEqual(33, result)
        mock_post.assert_called_once_with()

    @patch('twitter_bot.twitter_bot.TwitterBot.reply_to_mentions')
    def test_go_reply_to_mentions(self, mock_reply):
        mock_reply.return_value = 0

        result = self.runner.go(self.settings, 'reply_to_mentions')

        self.assertEqual(0, result)
        mock_reply.assert_called_once_with()
