import os
import unittest

from twitter_bot.since_id import FileSystemSinceIdProvider


class TestFileSystemSinceIdProvider(unittest.TestCase):

    def setUp(self):
        self.provider = FileSystemSinceIdProvider()
        self.provider.delete()
        os.remove(self.provider.filename)

    def test_get_since_id_none_exist(self):
        since_id = self.provider.get()

        self.assertEqual('', since_id)

    def test_get_since_id_exists(self):
        self.provider.set('33')

        since_id = self.provider.get()

        self.assertEqual('33', since_id)

    def test_set(self):
        self.provider.set('11')

        result = self.provider.set('22')

        self.assertFalse(result is None)
        self.assertEqual('22', self.provider.get())

    def test_delete(self):
        self.provider.set('11')

        result = self.provider.delete()

        self.assertFalse(result is None)
        self.assertEqual('', self.provider.get())
