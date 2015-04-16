import json
import logging
import os

import redis
from twitter import Twitter
from twitter.oauth import OAuth
from twitter.api import TwitterHTTPError

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)


def get_redis(redis_url=None):
    if not redis_url:
        redis_url = os.getenv('REDISTOGO_URL')
    return redis.Redis.from_url(redis_url)


class TwitterBot(object):

    def __init__(self, redis_url=None):
        OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
        self.DUPLICATE_CODE = 187

        self.twitter = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
                                          CONSUMER_KEY, CONSUMER_SECRET))
        self.redis = get_redis(redis_url)

    def get_error(self, base_message, hashtags=tuple()):
        message = base_message
        if len(hashtags) > 0:
            hashed_tags = ['#%s' % x for x in hashtags]
            hash_message = " ".join(hashed_tags)
            message = '%s matching %s' % (base_message, hash_message)
        return message

    def create_compliment(self, mentioner=None):
        sentence = self.redis.srandmember('sentences')
        adjective = self.redis.srandmember('adjectives')
        if not sentence or not adjective:
            return 'No compliments found.'
        message = sentence.decode('utf-8').format(adjective.decode('utf-8'))
        if mentioner:
            message = '%s %s' % (mentioner, message)
        return message

    def post_compliment(self, message, mention_id=None):
        code = 0
        try:
            self.twitter.statuses.update(status=message, in_reply_to_status_id=mention_id)
        except TwitterHTTPError as e:
            logging.error('Unable to post to twitter: %s' % e)
            response_data = json.loads(e.response_data.decode('utf-8'))
            code = response_data['errors'][0]['code']
        return code

    def reply_to_mentions(self):
        since_id = self.redis.get('since_id')
        logging.debug("Retrieved since_id: %s" % since_id)

        kwargs = {}
        if since_id:
            kwargs['since_id'] = since_id.strip()

        mentions = self.twitter.statuses.mentions_timeline(**kwargs)
        logging.info("Retrieved %s mentions" % len(mentions))

        mentions_processed = 0
        for mention in mentions:
            mention_id = mention['id']
            mentioner = '@%s' % mention['user']['screen_name']

            error_code = self.DUPLICATE_CODE
            tries = 0
            compliment = ''
            while error_code == self.DUPLICATE_CODE:
                if tries > 10:
                    logging.error('Unable to post duplicate message to %s: %s'
                                  % (mentioner, compliment))
                    break
                elif tries == 10:
                    compliment = self.get_error('No compliments found')
                else:
                    compliment = self.create_compliment(mentioner)
                error_code = self.post_compliment(compliment, mention_id)
                tries += 1

            mentions_processed += 1
            logging.info("Attempting to store since_id: %s" % mention_id)
            self.redis.set('since_id', mention_id)

        return mentions_processed

    def post_message(self):
        compliment = self.create_compliment()
        return self.post_compliment(compliment)
