import json
import logging
import os
import random

import pymongo
from twitter import Twitter
from twitter.oauth import OAuth
from twitter.api import TwitterHTTPError

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)


def get_mongo(mongo_uri=None, db_name='heartbot'):
    if not mongo_uri:
        mongo_uri = os.getenv('MONGOLAB_URI')
    mongo = pymongo.MongoClient(mongo_uri)
    if mongo:
        return mongo[db_name]
    return None


class TwitterBot(object):

    def __init__(self, mongo_uri=None, db_name=None):
        OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
        self.DUPLICATE_CODE = 187

        self.twitter = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
                                          CONSUMER_KEY, CONSUMER_SECRET))
        self.mongo = get_mongo(mongo_uri, db_name)

    def get_error(self, base_message, hashtags=tuple()):
        message = base_message
        if len(hashtags) > 0:
            hashed_tags = ['#%s' % x for x in hashtags]
            hash_message = " ".join(hashed_tags)
            message = '%s matching %s' % (base_message, hash_message)
        return message

    def create_compliment(self, mentioned=tuple()):
        num_records = self.mongo.sentences.count()
        if num_records < 1:
            return 'No compliments found.'
        index = random.randint(0, num_records-1)
        sentence = self.mongo.sentences.find().limit(1).skip(index)[0]
        message = sentence['sentence']
        if sentence['type']:
            word = self.mongo.words.find({'type': sentence['type']}).limit(1).skip(index)[0]
            message = message.format(word['word'])
        if len(mentioned):
            message = '%s %s' % (' '.join(sorted(mentioned)), message)
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
        since_id = self.mongo.since_id.find_one()
        logging.debug("Retrieved since_id: %s" % since_id)

        kwargs = {'count': 200}
        if since_id:
            kwargs['since_id'] = since_id['id']

        mentions = self.twitter.statuses.mentions_timeline(**kwargs)
        logging.info("Retrieved %s mentions" % len(mentions))

        mentions_processed = 0
        # We want to process least recent to most recent, so that since_id is set properly
        for mention in reversed(mentions):
            mention_id = mention['id']

            # Allow users to tweet compliments at other users, but don't include heartbotapp
            mentioned = set()
            mentioned.add('@%s' % mention['user']['screen_name'])
            for user in mention['entities']['user_mentions']:
                name = user['screen_name']
                if name != 'heartbotapp':
                    mentioned.add('@%s' % name)

            error_code = self.DUPLICATE_CODE
            tries = 0
            compliment = ''
            while error_code == self.DUPLICATE_CODE:
                if tries > 10:
                    logging.error('Unable to post duplicate message to %s: %s'
                                  % (mentioned, compliment))
                    break
                elif tries == 10:
                    compliment = self.get_error('No compliments found.')
                else:
                    compliment = self.create_compliment(mentioned)
                error_code = self.post_compliment(compliment, mention_id)
                tries += 1

            mentions_processed += 1
            logging.info("Attempting to store since_id: %s" % mention_id)
            self.mongo.since_id.remove()
            self.mongo.since_id.insert_one({'id': mention_id})

        return mentions_processed

    def post_message(self):
        compliment = self.create_compliment()
        return self.post_compliment(compliment)
