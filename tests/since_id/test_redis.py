import unittest

from mock import patch

from twitter_bot.since_id.redis_provider import RedisSinceIdProvider


class TestRedisProvider(unittest.TestCase):

    def setUp(self):
        self.provider = RedisSinceIdProvider(redis_url='redis://:@localhost:6379/10')
        self.provider.delete()

    @patch('os.environ.get')
    def test_constructor_empty_redis_env_var(self, mock_env_get):
        mock_env_get.return_value = 'bogus'

        provider = RedisSinceIdProvider()

        self.assertTrue(provider.redis is not None)

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
