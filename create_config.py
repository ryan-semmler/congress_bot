from pprint import pformat


def at(handle):
    return '@' * (not handle.startswith('@')) + handle


def create_config(action='close'):
    template = \
    """propublica_header = {}

# "consumer_key" is the API key. "Consumer_secret" is the API secret.
twitter_config = {}

handle = '{}'
max_tweet_len = 280

state = '{}'
include_rep = {}
district = {}

# Bot won't look at data from api older than this or store old tweets longer than this.
days_old_limit = 4

# Assign True to use govtrack url for bills, False for congress.gov
use_govtrack = True

# Log output to tweet_log.txt
output_to_file = True

# Use members' twitter handles instead of names when possible
tag_member = False
"""

    input("This program will create the configuration file needed to run Congress Bot.\n"
          "Before continuing, make sure you've created a Twitter account and gotten an API key for that account.\n"
          "You'll need your API keys for Twitter and Propublica to continue.\n\nPress ENTER to continue")

    handle = at(input("Enter the bot's twitter handle: "))
    state = input("Enter your state's two-letter abbreviation: ").lower()

    include_rep = 'y' in input("Include House member data in Twitter updates? y/n: ").lower()
    if include_rep:
        district = input("Enter the number of the Congressional district used for the bot: ")
    else:
        district = None

    propublica_header = {'X-API-Key': input('Enter your Propublica API key: ')}

    consumer_key = input("There are four required keys for the Twitter API: "
                         "consumer key, consumer secret, access token, and access token secret.\n"
                         "Enter the consumer key: ")
    consumer_secret = input("Enter the consumer secret: ")
    access_token = input("Enter the access token: ")
    access_token_secret = input("Enter the access token secret: ")

    twitter_config = pformat({'consumer_key': consumer_key,
                              'consumer_secret': consumer_secret,
                              'access_token': access_token,
                              'access_token_secret': access_token_secret})

    with open("config.py", 'w') as f:
        f.write(template.format(propublica_header, twitter_config, handle, state,
                                include_rep, district))

    input("\nConfig file set up successfully.\n"
          "Open config.py to manually change other settings.\n"
          "Press ENTER to {}".format(action))


if __name__ == '__main__':
    create_config()
