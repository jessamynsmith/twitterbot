heartbot
========

[![Build Status](https://travis-ci.org/jessamynsmith/heartbot.svg?branch=master)](https://travis-ci.org/jessamynsmith/heartbot)
[![Coverage Status](https://coveralls.io/repos/jessamynsmith/heartbot/badge.svg?branch=master)](https://coveralls.io/r/jessamynsmith/heartbot?branch=master)

Replies to any twitter mentions with a compliment. This project is already set up to be deployed to heroku.

Note: Must set up 4 environment variables:
- TWITTER_CONSUMER_KEY
- TWITTER_CONSUMER_SECRET
- TWITTER_OAUTH_SECRET
- TWITTER_OAUTH_TOKEN

Add Compliments
---------------

Edit bin/initialize_data.py and add compliments as desired. You can substitute up to one word (noun
or adjective) per sentence. The type field indicates what type of word to substitute. You can also
add a sentence to be used as-is, by specifying type=None. E.g.:
 
    sentences = [{'type': 'adjective', 'sentence': 'I really appreciate how {} you are.'},
                 ...
                 {'type': None, 'sentence': 'My world is a better place with you in it.'}]

I'm happy to merge pull requests with appropriate compliments!

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

    ./bin/initialize_data.py            # Clears any current data and adds compliments to datastore
    ./bin/run_bot.sh reply_to_mentions  # Check twitter stream for mentions, and reply
    ./bin/run_bot.sh post_message       # Post a message to twitter
