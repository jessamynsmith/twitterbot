import os
from redis import Redis

from twitter_bot.since_id.base_provider import BaseSinceIdProvider


class RedisSinceIdProvider(BaseSinceIdProvider):

    def __init__(self, redis_url=''):
        super(RedisSinceIdProvider, self).__init__()

        if not redis_url:
            redis_url = os.environ.get('REDIS_URL', '')
        self.redis = Redis.from_url(redis_url)

    def get(self):
        since_id = ''
        value = self.redis.get('since_id')
        if value:
            since_id = value.decode('utf8')
        return since_id

    def set(self, since_id):
        return self.redis.set('since_id', since_id)

    def delete(self):
        return self.redis.delete('since_id')


__all__ = ["RedisSinceIdProvider"]
