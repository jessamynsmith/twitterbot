#!/usr/bin/env python

import sys

from twitter_bot import settings
from twitter_bot.twitter_bot import TwitterBot


def run(settings_module, command):
    bot = TwitterBot(settings_module)

    result = 1
    if command == 'post_message':
        result = bot.post_message()
    elif command == 'reply_to_mentions':
        result = bot.reply_to_mentions()
    else:
        print("Command must be either 'post_message' or 'reply_to_mentions'")

    return result


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("You must specify a single command, either 'post_message' or 'reply_to_mentions'")
        res = 1
    else:
        res = run(settings, sys.argv[1])
    if res != 0:
        sys.exit(res)
