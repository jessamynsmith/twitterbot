import unittest

from twitter_bot import messages

MARKOV_TEXT = "a b c d"

class TestMarkovChain(unittest.TestCase):

    def test_instantiate(self):
        chain = messages.MarkovChainMessageProvider(MARKOV_TEXT)

    def test_a_random_word(self):
        chain = messages.MarkovChainMessageProvider(MARKOV_TEXT)
        word = chain.a_random_word()
        self.assertTrue(word in ["a", "b", "c", "d"])

    def test_a_random_word_with_args(self):
        chain = messages.MarkovChainMessageProvider(MARKOV_TEXT)
        word = chain.a_random_word("a")
        self.assertEqual("b", word)

    def test_create_message(self):
        chain = messages.MarkovChainMessageProvider(MARKOV_TEXT)
        message = chain.create(None)
        self.assertTrue(message)
        self.assertTrue(len(message) < 140)
