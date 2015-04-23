TwitterBot
==========

|Build Status| |Coverage Status| |PyPI Version| |Supported Versions| |Downloads|

Easy-to-use TwitterBot that posts new messages and replies to mentions.
Built on the popular twitter_ package.

Features
--------

You can use Twitterbot to:
 - Post a new message.
 - Reply to any twitter mentions with a message.

Installation
------------

You can get twitterbot from PyPI with:

::

    pip install twitterbot

The development version can be installed with:

::

    pip install -e git://github.com/jessamynsmith/twitterbot.git#egg=twitterbot

If you are developing locally, your version can be installed from the
project directory with:

::

    python setup.py.install

Usage
-----

**Quick Start**

By default, settings are populated from environment variables. The authentication variables
are required and can be `obtained from your Twitter account`_.

- TWITTER\_CONSUMER\_KEY
- TWITTER\_CONSUMER\_SECRET
- TWITTER\_OAUTH\_SECRET
- TWITTER\_OAUTH\_TOKEN

You can optionally set the following environment variables:

- TWITTER_MESSAGE_PROVIDER
   Provides messages to be posted. Defaults to 'messages.HelloWorldMessageProvider',
   a simple provider that always returns "Hello World!"
- TWITTER_SINCE_ID_PROVIDER
   Provides storage for since_id. Twitter uses sinFile in which to store last retrieved since_id. Defaults to using the filesystem
   ('./.since_id.txt'). You may set a value in the file to start handling mentions
   at a particular message id.
- TWITTER_DRY_RUN
   If set to True, messages will be logged rather than actually posting them to Twitter.

**Setting a Custom Message Provider**

You can inject your own message provider by setting the following environment variable:

::

    TWITTER_MESSAGE_PROVIDER = 'bot.messages.MyMessageProvider'

You would then need to create a bot.messages module with a
MyMessageProvider class that implements the ``create()`` method,
e.g.

::

    class MyMessageProvider(object):

        def create(self, mention):
            """
            Create a message
            :param mention: JSON object containing mention details from Twitter
            :return: a message
            """
            return "This is my message!"

**Setting a Custom Since_id Provider**

You can inject your own since_id provider (e.g. using redis) by setting the following
environment variable:

::

    TWITTER_SINCE_ID_PROVIDER = 'bot.since_id.RedisProvider'

You would then need to create a bot.since_id module with a RedisProvider class
that implements the ``get()``, ``set()``, and ``delete()`` methods,
e.g.

::

    # since_id.py
    import os
    import redis
    from twitter_bot import SettingsError

    class RedisProvider(object):

        def __init__(self, redis_url=None):
            if not redis_url:
                redis_url = os.environ.get('REDISTOGO_URL')
                if not redis_url:
                    raise SettingsError("You must supply redis_url or set the REDISTOGO_URL "
                                        "environment variable.")
            self.redis = redis.Redis.from_url(redis_url)

        def get(self):
            return self.redis.get('since_id')

        def set(self, since_id):
            return self.redis.set('since_id', since_id)

        def delete(self):
            return self.redis.delete('since_id')

**Overriding Settings**

If you require more control over settings, you can subclass Settings:

::

    from twitter_bot import Settings

    class MyBotSettings(Settings):
        def __init__(self):
            super(MyBotSettings, self).__init__()
            self.MESSAGE_PROVIDER = 'bot.messages.MyProvider'

**Automating the bot**

To run the bot as a cron job or Heroku scheduler task, you can make make a small script that
uses the provided runner. If you have customized settings, import your own settings class rather
than the provided settings.

::

    #!/usr/bin/env python
    # runner.py

    import sys

    from twitter_bot import BotRunner, Settings

    if __name__ == '__main__':
        if len(sys.argv) != 2:
            print("You must specify a single command, either 'post_message' or 'reply_to_mentions'")
            result = 1
        else:
            result = BotRunner().go(Settings(), sys.argv[1])
        sys.exit(result)

Then call the script as follows:

::

    $ ./runner.py post_message
    $ ./runner.py reply_to_mentions

Development
-----------

Get source:

::

    git clone https://github.com/jessamynsmith/twitterbot

Set up virtualenv:

::

    mkvirtualenv twitterbot --python=/path/to/python3
    pip install -r requirements/test.txt

Run tests:

::

    coverage run -m nose
    coverage report

Run bot:

::

    $ ./runner.py reply_to_mentions  # Check twitter stream for mentions, and reply
    $ ./runner.py post_message       # Post a message to twitter

.. |Build Status| image:: https://circleci.com/gh/jessamynsmith/twitterbot.svg?style=shield
   :target: https://circleci.com/gh/jessamynsmith/twitterbot
.. |Coverage Status| image:: https://coveralls.io/repos/jessamynsmith/twitterbot/badge.svg?branch=master
   :target: https://coveralls.io/r/jessamynsmith/twitterbot?branch=master
.. |PyPI Version| image:: https://pypip.in/version/twitterbot/badge.svg
   :target: https://pypi.python.org/pypi/twitterbot
.. |Supported Versions| image:: https://pypip.in/py_versions/twitterbot/badge.svg
   :target: https://pypi.python.org/pypi/twitterbot
.. |Downloads| image:: https://pypip.in/download/twitterbot/badge.svg
   :target: https://pypi.python.org/pypi/twitterbot
.. _`obtained from your Twitter account`: https://dev.twitter.com/oauth/overview/application-owner-access-tokens/
.. _twitter: https://pypi.python.org/pypi/twitter
