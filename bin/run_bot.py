#!/usr/bin/env python

import sys

import settings
from twitter_bot.twitter_bot import TwitterBot


def main(settings_module, args):
    error = "You must specify a single command, either 'post_message' or 'reply_to_mentions'"

    if len(args) != 2:
        print(error)
        return 1

    command = args[1]
    bot = TwitterBot(settings_module)

    result = 0
    if command == 'post_message':
        result = bot.post_message()
    elif command == 'reply_to_mentions':
        result = bot.reply_to_mentions()
    else:
        print(error)
        result = 2

    return result


if __name__ == '__main__':
    res = main(settings, sys.argv)
    if res != 0:
        sys.exit(res)
