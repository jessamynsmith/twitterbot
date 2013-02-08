import unittest
from mock import patch, Mock

from twitterbot.twitter_bot import TwitterBot


class TestTwitterBot(unittest.TestCase):

    MESSAGE = "You don't manage people, you manage things. You lead people. - Grace Hopper"

    def setUp(self):
        self.bot = TwitterBot(redis_url='redis://:@localhost:6379/10',
                              quotation_url='http://invalid/quotation/?')

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
        messages = self.bot.tokenize(self.MESSAGE, 80, '@js')

        self.assertEqual(1, len(messages))
        self.assertEqual('@js %s' % self.MESSAGE, messages[0])

    def test_tokenize_much_too_long_with_mention(self):
        messages = self.bot.tokenize(self.MESSAGE, 40, '@js')

        self.assertEqual(4, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 35)
        self.assertEqual("@js You don't manage people, ...", messages[0])
        self.assertEqual("@js ... you manage things. You ...", messages[1])
        self.assertEqual("@js ... lead people. - Grace ...", messages[2])
        self.assertEqual("@js ... Hopper", messages[3])

    def test_get_error_no_hashtags(self):
        error = self.bot.get_error('An error has occurred', [])

        self.assertEqual('An error has occurred', error)

    def test_get_error_with_hashtags(self):
        error = self.bot.get_error('An error has occurred', ['love', 'hate'])

        self.assertEqual('An error has occurred matching #love #hate', error)

    @patch('requests.get')
    def test_retrieve_quotation_success(self, mock_get):
        mock_result = Mock(status_code=200)
        mock_result.json.return_value = {'objects': [{
            'text': 'Here I stay',
            'author': {'name': 'Henrietta'}
        }]}
        mock_get.return_value = mock_result

        quotation = self.bot.retrieve_quotation([])

        self.assertEqual('Here I stay - Henrietta', quotation)
        mock_get.assert_called_with('http://invalid/quotation/?')

    @patch('requests.get')
    def test_retrieve_quotation_with_hashtags_success(self, mock_get):
        mock_result = Mock(status_code=200)
        mock_result.json.return_value = {'objects': [{
            'text': 'Here I stay',
            'author': {'name': 'Henrietta'}
        }]}
        mock_get.return_value = mock_result

        quotation = self.bot.retrieve_quotation(['stay'])

        self.assertEqual('Here I stay - Henrietta', quotation)
        mock_get.assert_called_with('http://invalid/quotation/?&text__icontains=stay')

    @patch('requests.get')
    def test_retrieve_quotation_no_quotations(self, mock_get):
        mock_result = Mock(status_code=200)
        mock_result.json.return_value = {'objects': []}
        mock_get.return_value = mock_result

        quotation = self.bot.retrieve_quotation([])

        self.assertEqual('No quotations found', quotation)
        mock_get.assert_called_with('http://invalid/quotation/?')

    @patch('requests.get')
    def test_retrieve_quotation_error_no_hashtags(self, mock_get):
        mock_get.return_value = Mock(status_code=500)

        quotation = self.bot.retrieve_quotation([])

        self.assertEqual('No quotations found', quotation)
        mock_get.assert_called_with('http://invalid/quotation/?')

    @patch('requests.get')
    def test_retrieve_quotation_error_with_hashtags(self, mock_get):
        mock_get.return_value = Mock(status_code=500)

        quotation = self.bot.retrieve_quotation(['love', 'hate'])

        self.assertEqual('No quotations found matching #love #hate', quotation)
        mock_get.assert_called_with('http://invalid/quotation/?&text__icontains=love&text__icontains=hate')
