TwitterBot
==========

|Build Status| |Coverage Status|

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
- TWITTER_SINCE_ID_FILENAME
   File in which to store last retrieved since_id. Defaults to './.since_id.txt'
   You may want to add this to your .gitignore file. You may set the value in the file
   to start handling mentions at a particular message id.

**Customization**

You can inject your own message provider by setting the following environment variable:

::

    TWITTER_MESSAGE_PROVIDER = 'bot.messages.MyMessageProvider'

You would then need to create a messages module with a
MyMessageProvider class that implements the ``create()`` method,
e.g.

::

    class MyMessageProvider(object):

        def create(self):
            return "This is my message!"

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

    from twitter_bot import Runner, Settings

    if __name__ == '__main__':
        if len(sys.argv) != 2:
            print("You must specify a single command, either 'post_message' or 'reply_to_mentions'")
            result = 1
        else:
            result = Runner().go(Settings(), sys.argv[1])
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
.. _`obtained from your Twitter account`: https://dev.twitter.com/oauth/overview/application-owner-access-tokens/
.. _twitter: https://pypi.python.org/pypi/twitter
