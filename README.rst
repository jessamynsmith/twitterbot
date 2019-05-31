TwitterBot
==========

|Build Status| |Coverage Status| |PyPI Version| |Supported Python Versions| |Downloads|

Easy-to-use TwitterBot that posts new messages and replies to mentions.
Built on the popular twitter_ package. Please read Twitter's
`Automation rules and best practices`_ before setting up a bot.

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
are required and can be `obtained from your Twitter account`_. It is recommended that you read
Twitter's `Automation rules and best practices`_ before setting up a bot.

- TWITTER\_CONSUMER\_KEY
- TWITTER\_CONSUMER\_SECRET
- TWITTER\_OAUTH\_SECRET
- TWITTER\_OAUTH\_TOKEN

You can optionally set the following environment variables:

- TWITTER_MESSAGE_PROVIDER
   Provides messages to be posted. Defaults to 'messages.HelloWorldMessageProvider',
   a simple provider that always returns "Hello World!"
- TWITTER_SINCE_ID_PROVIDER
   Provides storage for since_id. Twitter uses sinFile in which to store last retrieved since_id.
   Defaults to using the filesystem ('./.since_id.txt'). You may set a value in the file to
   start handling mentions at a particular message id.
- TWITTER_DRY_RUN
   If set to True, messages will be logged rather than actually posting them to Twitter.

The underquotedbot project is a `working example`_ of using the twitterbot library to build a
bot that is deployed to heroku and runs the twitter account `@the_underquoted`_.

**Setting a Custom Message Provider**

You can inject your own message provider by setting the following environment variable:

::

    export TWITTER_MESSAGE_PROVIDER='bot.messages.MyMessageProvider'

You would then need to create a bot.messages module with a
MyMessageProvider class that implements the ``create()`` method,
e.g.

::

    class MyMessageProvider(object):

        def create(self, mention, max_message_length):
            """
            Create a message
            :param mention: JSON object containing mention details from Twitter
            :param max_message_length: Maximum allowable length for created message
            :return: a message
            """
            return "This is my message!"

**Setting a Custom Since_id Provider**

The default is to use the FileSystemSinceIdProvider. Using the file system will NOT work correctly
on Heroku or any other host with an ephemeral file system. If you cannot rely on the file system,
you MUST specify a different SinceIdProvider.

TwitterBot comes with a Redis provider. By default, localhost will be used for redis. To use it, 
you must first install redis on your system. I recommend using homebrew on OSX:

::

    brew install redis
    brew services start redis

Once you have redis installed or available as a service, you can install the python redis package and set
environment variables to configure the provider. 

::

    pip install redis
    export TWITTER_SINCE_ID_PROVIDER='twitter_bot.since_id.redis_provider.RedisSinceIdProvider'
    export REDIS_URL=redis://:@somehost:someport # Optional, defaults to localhost

You can inject a custom since_id provider by setting the following environment variable:

::

    export TWITTER_SINCE_ID_PROVIDER='bot.since_id.MySinceIdProvider'

You would then need to create a bot.since_id module with a MySinceIdProvider class
that implements the ``get()``, ``set()``, and ``delete()`` methods,
e.g.

::

    # since_id.py
    import os
    from twitter_bot import SettingsError
    from twitter_bot import BaseSinceIdProvider

    class MySinceIdProvider(BaseSinceIdProvider):

        def __init__(self, source=None):
            if not source:
                source = os.environ.get('TWITTER_SINCE_ID_SOURCE')
                if not source:
                    raise SettingsError("You must supply source or set the TWITTER_SINCE_ID_SOURCE "
                                        "environment variable.")
            self.source = source

        def get(self):
            return self.source.get('since_id')

        def set(self, since_id):
            return self.source.set('since_id', since_id)

        def delete(self):
            return self.source.delete('since_id')

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

Fork the project on github and git clone your fork, e.g.:

::

    git clone https://github.com/<username>/twitterbot.git

Set up virtualenv:

::

    mkvirtualenv twitterbot
    pip install -r requirements/package.txt -r requirements/test.txt

Run tests with coverage (should be 100%) and check code style:

::

    coverage run -m nose
    coverage report -m
    flake8

Verify all supported Python versions:

::

    pip install tox
    tox

Run bot:

::

    $ ./bin/runner.py reply_to_mentions  # Check twitter stream for mentions, and reply
    $ ./bin/runner.py post_message       # Post a message to twitter


### Validating The Project Locally

The CircleCI build can be validated locally, using the CircleCI CLI and docker. 

First, install `Docker Desktop`_

Then, install the CircleCI CLI, e.g. using homebrew on OSX:

    brew install circleci

Then, you can validate it by running this command in the terminal:

    circleci config validate

Once you know your config is valid, you can test it.
The CLI allows you to run a single job from CircleCI on your desktop using docker:

    circleci local execute --job build

For more information, see the [CircleCI docs](https://circleci.com/docs/2.0/local-cli/#validate-a-circleci-config)


.. |Build Status| image:: https://img.shields.io/circleci/project/github/jessamynsmith/twitterbot.svg
   :target: https://circleci.com/gh/jessamynsmith/twitterbot
   :alt: Build status
.. |Coverage Status| image:: https://img.shields.io/coveralls/jessamynsmith/twitterbot.svg
   :target: https://coveralls.io/r/jessamynsmith/twitterbot?branch=master
   :alt: Coverage status
.. |PyPI Version| image:: https://img.shields.io/pypi/v/twitterbot.svg
   :target: https://pypi.python.org/pypi/twitterbot
   :alt: Latest PyPI version
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/twitterbot.svg
   :target: https://pypi.python.org/pypi/twitterbot
   :alt: Supported Python versions
.. |Downloads| image:: https://img.shields.io/pypi/dm/twitterbot.svg
   :target: https://pypi.python.org/pypi/twitterbot
   :alt: Number of PyPI downloads
.. _`Automation rules and best practices`: https://support.twitter.com/articles/76915-automation-rules-and-best-practices
.. _`working example`: https://github.com/jessamynsmith/underquotedbot
.. _`@the_underquoted`: https://twitter.com/the_underquoted/
.. _`obtained from your Twitter account`: https://dev.twitter.com/oauth/overview/application-owner-access-tokens/
.. _twitter: https://pypi.python.org/pypi/twitter
.. _`Docker Desktop`: https://www.docker.com/products/docker-desktop
