import unittest

from twitter_bot import tokenize


class TestQuotationBot(unittest.TestCase):

    MESSAGE = "You don't manage people, you manage things. You lead people. - Grace Hopper"

    def test_tokenize_short(self):
        messages = tokenize(self.MESSAGE, 80)

        self.assertEqual(1, len(messages))
        self.assertEqual(self.MESSAGE, messages[0])

    def test_tokenize_too_long(self):
        messages = tokenize(self.MESSAGE, 50)

        self.assertEqual(2, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 50)
        self.assertEqual("You don't manage people, you manage things. ...", messages[0])
        self.assertEqual("...You lead people. - Grace Hopper", messages[1])

    def test_tokenize_much_too_long(self):
        messages = tokenize(self.MESSAGE, 30)

        self.assertEqual(4, len(messages))
        for message in messages:
            self.assertTrue(len(message) <= 30)
        self.assertEqual("You don't manage people, ...", messages[0])
        self.assertEqual("...you manage things. You ...", messages[1])
        self.assertEqual("...lead people. - Grace ...", messages[2])
        self.assertEqual("...Hopper", messages[3])
