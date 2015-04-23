import os
import random
from . import settings

class HelloWorldMessageProvider(object):

    def create(self, mention):
        """
        Create a message
        :param mention: JSON object containing mention details from Twitter (or an empty dict {})
        :return: a message
        """
        return "Hello World!"


class MarkovChainMessageProvider(object):

    def __init__(self, text=None):
        text_path = os.environ.get('TWITTER_MARKOV_TEXT_PATH')
        if not (text or text_path):
            raise settings.SettingsError("Must specify Markov text path. This "
                "is loaded from the TWITTER_MARKOV_TEXT_PATH environment "
                "variable.")

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

    def create(self, mention):
        message = []

        def message_len():
            return sum([len(w) + 1 for w in message])

        while message_len() < 140:
            message.append(self.a_random_word(message[-1] if message else None))

        return ' '.join(message[:-1])

__all__ = ["HelloWorldMessageProvider", "MarkovChainMessageProvider"]
