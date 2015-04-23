import unittest
from mock import patch

from twitter_bot import messages, settings


class TestMarkovChainMessageProvider(unittest.TestCase):

    def setUp(self):
        self.provider = messages.MarkovChainMessageProvider("a b c d")

    @patch('os.environ.get')
    def test_constructor_empty_markov_text_path(self, mock_env_get):
        mock_env_get.return_value = ''

        try:
            messages.MarkovChainMessageProvider()
            self.fail("Should not be able to instantiate provider without markov text path")
        except settings.SettingsError as e:
            error = ("Must specify Markov text path. This is loaded from the "
                     "TWITTER_MARKOV_TEXT_PATH environment variable.")
            self.assertEqual(error, '{0}'.format(e))

    def test_a_random_word(self):
        word = self.provider.a_random_word()

        self.assertTrue(word in ["a", "b", "c", "d"])

    def test_a_random_word_with_args(self):
        word = self.provider.a_random_word("a")

        self.assertEqual("b", word)

    def test_create_message(self):
        max_message_length = 140

        message = self.provider.create(None, max_message_length)

        self.assertTrue(message)
        self.assertTrue(len(message) < max_message_length)
