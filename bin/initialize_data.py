from twitterbot.twitter_bot import get_redis


def add_data(redis, key, data):
    for item in data:
        redis.sadd(key, item.encode('utf-8'))

redis = get_redis('127.0.0.1:6379')

redis.delete('adjectives', 'sentences')

adjectives = ('smart', 'helpful', 'kind', 'hard-working', 'meticulous', 'diligent')
add_data(redis, 'adjectives', adjectives)

sentences = ('I really appreciate how {} you are.',
             'I am super inspired by how {} you are.',
             'I am so impressed by how {} you are.')
add_data(redis, 'sentences', sentences)
