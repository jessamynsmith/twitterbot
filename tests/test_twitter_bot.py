import unittest
from mock import call, patch, MagicMock
from twitter.api import TwitterHTTPError

from twitterbot.twitter_bot import TwitterBot


class TestTwitterBot(unittest.TestCase):

    def setUp(self):
        self.bot = TwitterBot(redis_url='redis://:@localhost:6379/10')

    @patch('redis.Redis.from_url')
    def test_constructor_no_urls(self, mock_from_url):
        mock_from_url.return_value = None

        bot = TwitterBot()

        self.assertEqual(None, bot.redis)

    def test_get_error_no_hashtags(self):
        error = self.bot.get_error('An error has occurred', [])

        self.assertEqual('An error has occurred', error)

    def test_get_error_with_hashtags(self):
        error = self.bot.get_error('An error has occurred', ['love', 'hate'])

        self.assertEqual('An error has occurred matching #love #hate', error)

    @patch('redis.Redis.srandmember')
    def test_create_compliment_success(self, mock_srandmember):
        mock_srandmember.side_effect = [b'I like how {} you are.', b'smart']

        compliment = self.bot.create_compliment()

        self.assertEqual('I like how smart you are.', compliment)

    @patch('redis.Redis.srandmember')
    def test_create_compliment_with_mentioner_success(self, mock_srandmember):
        mock_srandmember.side_effect = [b'I like how {} you are.', b'smart']

        compliment = self.bot.create_compliment('@jane')

        self.assertEqual('@jane I like how smart you are.', compliment)

    @patch('redis.Redis.srandmember')
    def test_create_compliment_error(self, mock_srandmember):
        mock_srandmember.return_value = None

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
        self.bot = TwitterBot(redis_url='redis://:@localhost:6379/10')
        self.bot.twitter.statuses = MagicMock()
        self.bot.create_compliment = MagicMock(return_value="You rock!")
        self.bot.post_compliment = MagicMock()
        self.bot.redis = MagicMock(get=MagicMock(return_value=None))

    def test_reply_to_mentions_no_mentions_no_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with()

    def test_reply_to_mentions_no_mentions_with_since_id(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = []
        self.bot.redis.get.return_value = '3'

        result = self.bot.reply_to_mentions()

        self.assertEqual(0, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_with(
            since_id='3')
        self.bot.redis.get.assert_called_once_with('since_id')

    def test_reply_to_mentions_error(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'hashtags': [{'text': 'love'}]}}
        ]
        self.bot.post_compliment.return_value = 187

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with()
        self.assertEqual(11, len(self.bot.post_compliment.mock_calls))
        self.assertEqual(call("You rock!", '123'),
                         self.bot.post_compliment.mock_calls[0])
        self.assertEqual(call('No compliments found', '123'),
                         self.bot.post_compliment.mock_calls[10])
        self.bot.redis.get.assert_called_once_with('since_id')
        self.bot.redis.set.assert_called_once_with('since_id', '123')

    def test_reply_to_mentions_success(self):
        self.bot.twitter.statuses.mentions_timeline.return_value = [
            {'id': '123',
             'user': {'screen_name': 'jessamyn'},
             'entities': {'hashtags': [{'text': 'love'}]}}
            ]
        self.bot.post_compliment.return_value = 0

        result = self.bot.reply_to_mentions()

        self.assertEqual(1, result)
        self.bot.twitter.statuses.mentions_timeline.assert_called_once_with()
        expected_calls = [call("You rock!", '123')]
        self.assertEqual(expected_calls, self.bot.post_compliment.mock_calls)
        self.bot.redis.get.assert_called_once_with('since_id')
        self.bot.redis.set.assert_called_once_with('since_id', '123')

    def test_post_message(self):
        self.bot.post_compliment.return_value = 0

        result = self.bot.post_message()

        self.assertEqual(0, result)
        self.bot.post_compliment.assert_called_once_with("You rock!")
