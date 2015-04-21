twitterbot
========

[![Build Status](https://circleci.com/gh/jessamynsmith/twitterbot.svg?style=shield)](https://circleci.com/gh/jessamynsmith/twitterbot)
[![Coverage Status](https://coveralls.io/repos/jessamynsmith/twitterbot/badge.svg?branch=master)](https://coveralls.io/r/jessamynsmith/twitterbot?branch=master)

Provides tasks to do the following:
- Reply to any twitter mentions with a message.
- Post a message.
 
This project is set up to build on circleci.

Note: Must set up 4 environment variables from an oauth-enabled Twitter account:
- TWITTER_CONSUMER_KEY
- TWITTER_CONSUMER_SECRET
- TWITTER_OAUTH_SECRET
- TWITTER_OAUTH_TOKEN

MessageProvider
---------------

You can inject your own message provider via settings.py, e.g.

```
MESSAGES_PROVIDER = 'messages.messages.HelloWorldMessageProvider'
```

You would then need to create a messages.messages module with a 
HelloWorldMessageProvider class that implements the ```create()``` method, e.g.

```
class HelloWorldMessageProvider(object):

    def create(self):
        return "Hello World!"
```

Development
-----------

Get source:

    git clone https://github.com/jessamynsmith/twitterbot

Set up virtualenv:

    mkvirtualenv twitterbot --python=/path/to/python3
    pip install -r requirements/development.txt

Run tests:

    coverage run -m nose
    coverage report

Run bot:

    ./bin/run_bot.sh reply_to_mentions  # Check twitter stream for mentions, and reply
    ./bin/run_bot.sh post_message       # Post a message to twitter
