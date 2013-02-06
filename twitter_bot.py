import logging
import os
import requests
import string
from twitter import Twitter
from twitter.oauth import OAuth

import settings

logging.basicConfig(filename=settings.LOG_FILE, level=logging.DEBUG)


def tokenize(message, message_length):
    if len(message) < message_length:
        return [message]

    max_length = message_length - 4
    tokens = message.split(' ')
    indices = []
    index = 1
    length = len(tokens[0])
    for i in range(1, len(tokens)):
        if length + 1 + len(tokens[i]) >= max_length:
            indices.append(index)
            length = 3 + len(tokens[i])
        else:
            length += 1 + len(tokens[i])
        index += 1

    indices.append(index)

    messages = [string.join(tokens[0:indices[0]], ' ')]
    for i in range(1, len(indices)):
        messages[i-1] += ' ...'
        messages.append("...%s" % string.join(tokens[indices[i-1]:indices[i]], ' '))

    return messages


def format_message(quotation, mentioner):
    message = ''
    if mentioner:
        message = '@%s ' % mentioner
    message += '%s - %s' % (quotation['text'], quotation['author']['name'])
    return message


def quotation_main():

    OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
    OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
    CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

    twitter = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
                                 CONSUMER_KEY, CONSUMER_SECRET))

    since_id_file = open(settings.SINCE_ID_FILE)
    since_id = since_id_file.readline()
    since_id_file.close()
    logging.debug("Retrieved since_id: %s" % since_id)

    kwargs = {}
    if since_id:
        kwargs['since_id'] = since_id.strip()

    mentions = twitter.statuses.mentions_timeline(**kwargs)
    logging.debug("Retrieved %s mentions" % len(mentions))

    mention_id = None
    for mention in mentions:
        mention_id = mention['id']
        mentioner = mention['user']['screen_name']

        result = requests.get(settings.QUOTATION_URL)
        logging.debug("Requested quote, status code=%s" % result.status_code)
        list = result.json()
        quotation = list['objects'][0]

        message = format_message(quotation, mentioner)
        logging.debug("Attempting to post message: %s" % message)

        messages = tokenize(message, 140)
        for message in messages:
            twitter.statuses.update(status=message)

    if mention_id:
        logging.debug("Attempting to store since_id: %s" % mention_id)
        since_id_file = open(settings.SINCE_ID_FILE, 'w')
        since_id_file.write('%s\n' % mention_id)
        since_id_file.close()


if __name__ == "__main__":
    quotation_main()

