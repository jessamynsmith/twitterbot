import logging
import os
import string

import redis
import requests
from twitter import Twitter
from twitter.oauth import OAuth
from twitter.api import TwitterHTTPError

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)


class TwitterBot(object):

    def __init__(self, redis_url=None, quotation_url=None):
        OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
        if not quotation_url:
            quotation_url = os.environ.get('QUOTATION_URL')
        self.BASE_URL = quotation_url
        self.DUPLICATE_CODE = 187

        self.twitter = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
                                          CONSUMER_KEY, CONSUMER_SECRET))

        if not redis_url:
            redis_url = os.getenv('REDISTOGO_URL')
        self.redis = redis.Redis.from_url(redis_url)

    def tokenize(self, message, message_length, mentioner=None):
        if mentioner:
            message = '%s %s' % (mentioner, message)
        if len(message) < message_length:
            return [message]

        # -4 for trailing ' ...'
        max_length = message_length - 4
        mentioner_length = 0
        if mentioner:
            # adjust for initial "@mentioner " on each message
            mentioner_length = len(mentioner) + 1
            max_length -= mentioner_length
        tokens = message.split(' ')
        indices = []
        index = 1
        length = len(tokens[0])
        for i in range(1, len(tokens)):
            if length + 1 + len(tokens[i]) >= max_length:
                indices.append(index)
                # 3 for leading "..."
                length = 3 + mentioner_length + len(tokens[i])
            else:
                length += 1 + len(tokens[i])
            index += 1

        indices.append(index)

        messages = [string.join(tokens[0:indices[0]], ' ')]
        for i in range(1, len(indices)):
            messages[i-1] += ' ...'
            parts = []
            if mentioner:
                parts.append(mentioner)
            parts.append("...")
            parts.extend(tokens[indices[i-1]:indices[i]])
            messages.append(string.join(parts, ' '))

        return messages

    def get_error(self, base_message, hashtags):
        message = base_message
        if len(hashtags) > 0:
            hashed_tags = ['#%s' % x for x in hashtags]
            hash_message = string.join(hashed_tags, ' ')
            message = '%s matching %s' % (base_message, hash_message)
        return message

    def retrieve_quotation(self, hashtags=[]):
        message = self.get_error('No quotations found', hashtags)

        url = self.BASE_URL
        for hashtag in hashtags:
            url = '%s&text__icontains=%s' % (url, hashtag)
        logging.debug("Trying URL: %s" % url)
        result = requests.get(url)
        logging.debug("Quotation request, status code=%s" % result.status_code)

        if result.status_code == 200:
            quotations = result.json()
            if len(quotations['objects']) > 0:
                quotation = quotations['objects'][0]
                message = '%s - %s' % (quotation['text'],
                                       quotation['author']['name'])

        return message

    def post_quotation(self, quotation, mentioner=None, mention_id=None):
        messages = self.tokenize(quotation, 140, mentioner)
        code = 0
        for message in messages:
            try:
                self.twitter.statuses.update(status=message,
                                             in_reply_to_status_id=mention_id)
            except TwitterHTTPError as e:
                code = e.response_data['errors'][0]['code']
                break
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

            hashtags = []
            for hashtag in mention['entities']['hashtags']:
                hashtags.append(hashtag['text'])

            error_code = self.DUPLICATE_CODE
            tries = 0
            while error_code == self.DUPLICATE_CODE:
                if tries > 10:
                    logging.error('Unable to post duplicate message to %s: %s'
                                  % (mentioner, quotation))
                    break
                elif tries == 10:
                    quotation = self.get_error('No quotations found', hashtags)
                else:
                    quotation = self.retrieve_quotation(hashtags)
                error_code = self.post_quotation(quotation, mentioner,
                                                 mention_id)
                tries += 1

            mentions_processed += 1
            logging.info("Attempting to store since_id: %s" % mention_id)
            self.redis.set('since_id', mention_id)

        return mentions_processed

    def post_message(self):
            quotation = self.retrieve_quotation()
            self.post_quotation(quotation)

