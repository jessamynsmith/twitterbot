import os


class SettingsError(Exception):
    pass


class Settings(object):
    """ Settings for TwitterBot
    You can use Settings as-is by setting environment variables, or subclass
    Settings to override values
    """
    def __init__(self):
        # Twitter settings (create a twitter account with oauth enabled to get values)
        self.OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
        self.OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
        self.CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
        self.CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

        # Provider for since_id. The since_id is used when retrieving mentions from
        # twitter; only new mentions since since_id will be retrieved. If no value is
        # specified, ALL available mentions will be retrieved.
        default = 'twitter_bot.since_id.FileSystemSinceIdProvider'
        self.SINCE_ID_PROVIDER = os.environ.get('TWITTER_SINCE_ID_PROVIDER', default)

        # Messages provider
        default = 'twitter_bot.messages.HelloWorldMessageProvider'
        self.MESSAGE_PROVIDER = os.environ.get('TWITTER_MESSAGE_PROVIDER', default)

        # Set to True to suppress actually sending messages.
        self.DRY_RUN = os.environ.get('TWITTER_DRY_RUN', False)


__all__ = ["Settings", "SettingsError"]
