import logging
import os
import redis
import requests
import string
from twitter import Twitter
from twitter.oauth import OAuth
import urlparse

import settings

logging.basicConfig(filename=settings.LOG_FILE, level=logging.DEBUG)


def tokenize(message, message_length, mentioner=None):
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


def format_message(quotation):
    message = '%s - %s' % (quotation['text'], quotation['author']['name'])
    return message


def quotation_main():

    OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
    OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
    CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

    twitter = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
                                 CONSUMER_KEY, CONSUMER_SECRET))

    url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
    uq_redis = redis.Redis(host=url.hostname, port=url.port, password=url.password)
    since_id = uq_redis.get('since_id')
    logging.debug("Retrieved since_id: %s" % since_id)

    kwargs = {}
    if since_id:
        kwargs['since_id'] = since_id.strip()

    mentions = twitter.statuses.mentions_timeline(**kwargs)
    logging.debug("Retrieved %s mentions" % len(mentions))

    mention_id = None
    for mention in mentions:
        mention_id = mention['id']
        mentioner = '@%s' % mention['user']['screen_name']

        query_args = []
        for hashtag in mention['entities']['hashtags']:
            query_args.append('text__contains=%s' % hashtag['text'])

        url = settings.QUOTATION_URL + '&' + string.join(query_args, '&')
        logging.debug("Trying URL: %s" % url)
        result = requests.get(url)
        logging.debug("Requested quote, status code=%s" % result.status_code)
        list = result.json()
        quotation = list['objects'][0]

        message = format_message(quotation)
        logging.debug("Attempting to post message: %s" % message)

        messages = tokenize(message, 140, mentioner)
        for message in messages:
            twitter.statuses.update(status=message,
                                    in_reply_to_status_id=mention_id)

    if mention_id:
        logging.debug("Attempting to store since_id: %s" % mention_id)
        uq_redis.set('since_id', mention_id)


if __name__ == "__main__":
    quotation_main()

