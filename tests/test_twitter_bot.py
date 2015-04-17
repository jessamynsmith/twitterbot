import unittest
from mock import call, patch, MagicMock
from twitter.api import TwitterHTTPError

from twitterbot.twitter_bot import TwitterBot


class TestTwitterBot(unittest.TestCase):

    def setUp(self):
        self.bot = TwitterBot(mongo_uri='mongodb://localhost/heartbottest')
        self.bot.mongo.sentences.remove()
        self.bot.mongo.words.remove()

    @patch('pymongo.MongoClient')
    def test_constructor_no_urls(self, mock_from_url):
        mock_from_url.return_value = None

        bot = TwitterBot()

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
        error.response_data = b'{"errors": [{"code": 187}]}'
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
        self.bot = TwitterBot(mongo_uri='mongodb://localhost/heartbottest')
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
