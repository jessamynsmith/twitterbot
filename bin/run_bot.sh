#!/bin/bash

# This script will quit on the first error that is encountered.
set -e

python twitter_bot/twitter_bot.py $1
