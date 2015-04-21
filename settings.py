# Settings for TwitterBot
import os

# Twitter settings (create a twitter account with oauth enabled to get values)
OAUTH_TOKEN = os.environ.get('TWITTER_OAUTH_TOKEN')
OAUTH_SECRET = os.environ.get('TWITTER_OAUTH_SECRET')
CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

# Mongo URI, local or remote
MONGO_URI = 'mongodb://127.0.0.1/local'

# Messages provider
MESSAGES_PROVIDER = 'messages.messages.HelloWorldMessageProvider'
