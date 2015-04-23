import unittest
from mock import patch

from twitter_bot import messages, settings


class TestBaseMessageProvider(unittest.TestCase):

    def test_extract_hashtags_empty_mention(self):
        provider = messages.BaseMessageProvider()

        hashtags = provider._extract_hashtags({})

        self.assertEqual([], hashtags)

    def test_extract_hashtags_with_hashtags(self):
        mention = {'entities': {'hashtags': [{'text': 'love'}, {'text': 'hate'}]}}
        provider = messages.BaseMessageProvider()

        hashtags = provider._extract_hashtags(mention)

        self.assertEqual(['love', 'hate'], hashtags)

    def test_create(self):
        provider = messages.BaseMessageProvider()

        try:
            provider.create({}, 20)
            self.fail("Should not be able to call create on abstract parent class")
        except NotImplementedError as e:
            self.assertEqual('Child class must implement create(self, mention)', '{0}'.format(e))


class TestHelloWorldMessageProvider(unittest.TestCase):

    def test_create(self):
        provider = messages.HelloWorldMessageProvider()

        message = provider.create({}, 20)

        self.assertEqual('Hello World!', message)


class TestMarkovChainMessageProvider(unittest.TestCase):

    def setUp(self):
        self.provider = messages.MarkovChainMessageProvider("a b c d")

    @patch('os.environ.get')
    def test_constructor_empty_markov_text_path(self, mock_env_get):
        mock_env_get.return_value = ''

        try:
            messages.MarkovChainMessageProvider()
            self.fail("Should not be able to instantiate provider without mongo")
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
