import unittest

from twitter_bot import messages


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
            self.fail("Should not be able to call create() on abstract parent class")
        except NotImplementedError as e:
            self.assertEqual('Child class must implement create(self, mention)', '{0}'.format(e))
