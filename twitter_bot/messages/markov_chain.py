import os
import random
from twitter_bot import settings

from twitter_bot.messages.base import BaseMessageProvider


class MarkovChainMessageProvider(BaseMessageProvider):

    def __init__(self, text=None):
        """
        :param text: String of text to be used for Markov chain generation
        :return: Instantiated provider
        """
        super(MarkovChainMessageProvider, self).__init__()

        text_path = os.environ.get('TWITTER_MARKOV_TEXT_PATH')
        if not (text or text_path):
            raise settings.SettingsError("Must specify Markov text path. This is loaded from "
                                         "the TWITTER_MARKOV_TEXT_PATH environment variable.")

        text = text or open(text_path, 'r').read()
        markov_dict = {}
        words = text.split()
        prev_word = words[0]
        for word in words[1:]:
            if not markov_dict.get(prev_word):
                markov_dict[prev_word] = []
            markov_dict[prev_word].append(word)
            prev_word = word

        self.markov_dict = markov_dict

    def a_random_word(self, prev_word=None):
        if prev_word and self.markov_dict.get(prev_word):
            return random.choice(self.markov_dict[prev_word])
        else:
            return random.choice(list(self.markov_dict.keys()))

    def create(self, mention, max_message_length):
        """
        Create a message
        :param mention: JSON object containing mention details from Twitter (or an empty dict {})
        :param max_message_length: Maximum allowable length for created message
        :return: A random message created using a Markov chain generator
        """
        message = []

        def message_len():
            return sum([len(w) + 1 for w in message])

        while message_len() < max_message_length:
            message.append(self.a_random_word(message[-1] if message else None))

        return ' '.join(message[:-1])


__all__ = ["MarkovChainMessageProvider"]
