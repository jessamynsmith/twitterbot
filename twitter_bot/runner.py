#!/usr/bin/env python

import sys

from twitter_bot import Runner, Settings


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("You must specify a single command, either 'post_message' or 'reply_to_mentions'")
        result = 1
    else:
        result = Runner().go(Settings(), sys.argv[1])
    sys.exit(result)
