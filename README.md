twitterbot
==========

Replies to any twitter mentions with a quotation

Note: Must set up 6 environment variables:
TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET
TWITTER_OAUTH_SECRET
TWITTER_OAUTH_TOKEN
LOG_FILE_PATH
QUOTATION_URL

for the underquoted, use the following QUOTATION_URL:
'https://underquoted.herokuapp.com/api/v1/quotations/?format=json&random=true&limit=1'

