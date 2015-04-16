heartbot
========

[![Build Status](https://travis-ci.org/jessamynsmith/heartbot.svg?branch=master)](https://travis-ci.org/jessamynsmith/heartbot)
[![Coverage Status](https://coveralls.io/repos/jessamynsmith/heartbot/badge.svg?branch=master)](https://coveralls.io/r/jessamynsmith/heartbot?branch=master)

Replies to any twitter mentions with a compliment. This project is already set up to be deployed to heroku.

Note: Must set up 5 environment variables:
- TWITTER_CONSUMER_KEY
- TWITTER_CONSUMER_SECRET
- TWITTER_OAUTH_SECRET
- TWITTER_OAUTH_TOKEN

Development
-----------

Get source:

    git clone https://github.com/jessamynsmith/heartbot

Set up virtualenv:

    mkvirtualenv heartbot --python=/path/to/python3
    pip install -r requirements/development.txt

Run tests:

    coverage run -m nose
    coverage report

Run bot:

    python bin/reply_to_mentions.py  # Check twitter stream for mentions, and reply
    python bin/post_message.py       # Post a message to twitter
