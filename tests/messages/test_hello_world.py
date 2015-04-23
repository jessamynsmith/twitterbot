import unittest

from twitter_bot import messages


class TestHelloWorldMessageProvider(unittest.TestCase):

    def test_create(self):
        provider = messages.HelloWorldMessageProvider()

        message = provider.create({}, 20)

        self.assertEqual('Hello World!', message)
