import unittest
from mock import patch, MagicMock

from twitter_bot.run_bot import run
from twitter_bot.twitter_bot import TwitterBot
from tests import settings_test


class TestRunBot(unittest.TestCase):
    def setUp(self):
        self.bot = TwitterBot(settings_test)
        self.bot.twitter.statuses = MagicMock()
        self.bot.post_compliment = MagicMock()
        self.bot.mongo.sentences.insert_one({'type': 'adjective', 'sentence': "You're {}."})
        self.bot.mongo.words.insert_one({'type': 'adjective', 'word': "smart"})
        self.bot.mongo.since_id.delete_many({})

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    @patch('pymongo.MongoClient')
    def test_run_invalid_arg(self, mock_mongo, mock_post):
        mock_mongo.return_value = None
        mock_post.return_value = 33

        result = run(settings_test, 'bogus')

        self.assertEqual(1, result)
        self.assertEqual(0, mock_post.call_count)

    @patch('twitter_bot.twitter_bot.TwitterBot.post_message')
    @patch('pymongo.MongoClient')
    def test_run_post_message(self, mock_mongo, mock_post):
        mock_mongo.return_value = None
        mock_post.return_value = 33

        result = run(settings_test, 'post_message')

        self.assertEqual(33, result)
        mock_post.assert_called_once_with()

    @patch('twitter_bot.twitter_bot.TwitterBot.reply_to_mentions')
    @patch('pymongo.MongoClient')
    def test_run_reply_to_mentions(self, mock_mongo, mock_reply):
        mock_mongo.return_value = None
        mock_reply.return_value = 0

        result = run(settings_test, 'reply_to_mentions')

        self.assertEqual(0, result)
        mock_reply.assert_called_once_with()
