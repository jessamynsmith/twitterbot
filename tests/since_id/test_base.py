import unittest

from twitter_bot.since_id import BaseSinceIdProvider


class TestBaseMessageProvider(unittest.TestCase):

    def setUp(self):
        self.provider = BaseSinceIdProvider()

    def test_get(self):
        try:
            self.provider.get()
            self.fail("Should not be able to call get() on abstract parent class")
        except NotImplementedError as e:
            self.assertEqual('Child class must implement get(self)', '{0}'.format(e))

    def test_set(self):
        try:
            self.provider.set(23)
            self.fail("Should not be able to call set() on abstract parent class")
        except NotImplementedError as e:
            self.assertEqual('Child class must implement set(self, since_id)', '{0}'.format(e))

    def test_delete(self):
        try:
            self.provider.delete()
            self.fail("Should not be able to call delete() on abstract parent class")
        except NotImplementedError as e:
            self.assertEqual('Child class must implement delete(self)', '{0}'.format(e))
