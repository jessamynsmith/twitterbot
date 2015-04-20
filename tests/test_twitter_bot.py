import unittest
from mock import call, patch, MagicMock
from twitter.api import TwitterHTTPError

from twitter_bot.twitter_bot import main, Settings, TwitterBot


class TestSettings(unittest.TestCase):

    @patch('os.environ.get')
    def test_constructor_invalid(self, mock_env_get):
        mock_env_get.return_value = None

        try:
            Settings()
            self.fail('Should not be able to construct settings with None values')
        except ValueError:
            pass

    @patch('os.environ.get')
    def test_constructor_valid(self, mock_env_get):
        mock_env_get.return_value = 'bogus'

        settings = Settings()

        self.assertEqual(['bogus', 'bogus', 'bogus', 'bogus'], settings)


class TestTwitterBot(unittest.TestCase):
    def setUp(self):
        self.settings = {'TWITTER_CONSUMER_KEY': 'bogus',
                         'TWITTER_CONSUMER_SECRET': 'bogus',
                         'TWITTER_OAUTH_SECRET': 'bogus',
                         'TWITTER_OAUTH_TOKEN': 'bogus'}
        self.bot = TwitterBot(self.settings, mongo_uri='mongodb://localhost/heartbottest')
        self.bot.mongo.sentences.remove()
        self.bot.mongo.words.remove()

    @patch('pymongo.MongoClient')
    def test_constructor_no_uri(self, mock_mongo):
        mock_mongo.return_value = None

        bot = TwitterBot(settings=self.settings)

        self.assertEqual(None, bot.mongo)

    def test_get_error_no_hashtags(self):
        error = self.bot.get_error('An error has occurred', [])

        self.assertEqual('An error has occurred', error)

    def test_get_error_with_hashtags(self):
        error = self.bot.get_error('An error has occurred', ['love', 'hate'])

        self.assertEqual('An error has occurred matching #love #hate', error)

    def test_create_compliment_success_simple(self):
        self.bot.mongo.sentences.insert_one({'type': None, 'sentence': "You're a bright light."})

        compliment = self.bot.create_compliment()

        self.assertEqual("You're a bright light.", compliment)

    def test_create_compliment_success_complex(self):
        self.bot.mongo.sentences.insert_one({'type': 'adjective', 'sentence': "You're {}."})
        self.bot.mongo.words.insert_one({'type': 'adjective', 'word': "smart"})

        compliment = self.bot.create_compliment()

        self.assertEqual("You're smart.", compliment)

    def test_create_compliment_success_with_mentioner(self):
        self.bot.mongo.sentences.insert_one({'type': None, 'sentence': "You're a bright light."})

        compliment = self.bot.create_compliment(('@jane',))

        self.assertEqual("@jane You're a bright light.", compliment)

    def test_create_compliment_error(self):
        compliment = self.bot.create_compliment()

        self.assertEqual('No compliments found.', compliment)

    def test_post_compliment_no_mention(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.post_compliment('You are a bright light.')

        self.assertEqual(0, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=None)

    def test_post_compliment_with_mention(self):
        mock_statuses = MagicMock()
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.post_compliment('You are a bright light.', mention_id=2)

        self.assertEqual(0, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=2)

    def test_post_compliment_unknown_error(self):
        error = TwitterHTTPError(
            MagicMock(headers={'Content-Encoding': ''}), '', '', [])
        error.response_data = {"errors": [{"code": 187}]}
        mock_update = MagicMock(side_effect=error)
        mock_statuses = MagicMock()
        mock_statuses.update = mock_update
        self.bot.twitter.statuses = mock_statuses

        result = self.bot.post_compliment('You are a bright light.')

        self.assertEqual(187, result)
        mock_statuses.update.assert_called_with(
            status='You are a bright light.', in_reply_to_status_id=None)


class TestReplyToMentions(unittest.TestCase):
    def setUp(self):
        self.settings = {'TWITTER_CONSUMER_KEY': 'bogus',
                         'TWITTER_CONSUMER_SECRET': 'bogus',
                         'TWITTER_OAUTH_SECRET': 'bogus',
                         'TWITTER_OAUTH_TOKEN': 'bogus'}
        self.bot = TwitterBot(self.settings, mongo_uri='mongodb://localhost/heartbottest')
        self.bot.twitter.statuses = MagicMock()
        self.bot.post_compliment = MagicMock()
        self.bot.mongo.sentences.insert_one({'type': 'adjective', 'sentence': "You're {}."})
        self.bot.mongo.words.insert_one({'type': 'adjective', 'word': "smart"})
        self.bot.mongo.since_id.remove()

    def test_reply_to_mentions_no_mentions_no_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(count=200)

    def test_reply_to_mentions_no_mentions_with_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []
        self.bot.mongo.since_id.insert_one({'id': '3'})

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(count=200, since_id='3')
        self.assertEqual([], self.bot.post_compliment.mock_calls)

    def test_reply_to_mentions_error(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'user_mentions': []}}
        ]
        self.bot.post_compliment.return_value = 187
        self.bot.mongo.sentences.remove()

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with(count=200)
        self.assertEqual(11, len(self.bot.post_compliment.mock_calls))
        self.assertEqual(call('No compliments found.', '123'),
                         self.bot.post_compliment.mock_calls[0])
        self.assertEqual(call('No compliments found.', '123'),
                         self.bot.post_compliment.mock_calls[10])

    def test_reply_to_mentions_success(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'user_mentions': [{'screen_name': 'heartbotapp'},
                                            {'screen_name': 'jill'}]}}
        ]
        self.bot.post_compliment.return_value = 0

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with(count=200)
        expected_calls = [call("@jessamyn @jill You're smart.", '123')]
        self.assertEqual(expected_calls, self.bot.post_compliment.mock_calls)

    def test_post_message(self):
        self.bot.post_compliment.return_value = 0

        result = self.bot.post_message()

        self.assertEqual(0, result)
        self.bot.post_compliment.assert_called_once_with("You're smart.")

    def test_main_no_args(self):
        result = main(self.settings, [])

        self.assertEqual(1, result)

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    @patch('pymongo.MongoClient')
    def test_main_invalid_arg(self, mock_mongo, mock_post):
        mock_mongo.return_value = None
        mock_post.return_value = 33

        result = main(self.settings, ['', 'bogus'])

        self.assertEqual(2, result)
        self.assertEqual(0, mock_post.call_count)

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    @patch('pymongo.MongoClient')
    def test_main_post_message(self, mock_mongo, mock_post):
        mock_mongo.return_value = None
        mock_post.return_value = 33

        result = main(self.settings, ['', 'post_message'])

        self.assertEqual(33, result)
        mock_post.assert_called_once_with()

    @patch('twitter_bot.twitter_bot.TwitterBot.reply_to_mentions')
    @patch('pymongo.MongoClient')
    def test_main_reply_to_mentions(self, mock_mongo, mock_reply):
        mock_mongo.return_value = None
        mock_reply.return_value = 0

        result = main(self.settings, ['', 'reply_to_mentions'])

        self.assertEqual(0, result)
        mock_reply.assert_called_once_with()
