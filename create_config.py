from pprint import pformat


def clean(handle):
    return handle['@' in handle:]


def create_config(action='close'):
    template = \
    """propublica_header = {}

# "consumer_key" is the API key. "Consumer_secret" is the API secret.
twitter_config = {}

handle = '{}'

state = '{}'
include_rep = {}

# Bot won't look at data from api older than this or store old tweets longer than this.
days_old_limit = 4

max_tweet_len = 280
"""

    input("This program will create the configuration file needed to run Congress Bot.\n"
          "Before continuing, make sure you've created a Twitter account and gotten an API key for that account.\n"
          "You'll need your API keys for Twitter and Propublica to continue.\n\nPress ENTER to continue")

    handle = clean(input("Enter the bot's twitter handle: "))
    state = input("Enter your state's two-letter abbreviation: ").lower()

    include_rep_raw = 'y' in input("Include House member data in Twitter updates? y/n: ").lower()
    if include_rep_raw:
        include_rep = str(include_rep_raw) + "\ndistrict = {}".format(
            input("Enter the number of the Congressional district used for the bot: "))
    else:
        include_rep = include_rep_raw

    ppublica = input('Enter your Propublica API key: ')
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

    propublica_header = {'X-API-Key': ppublica}

    with open("config.py", 'w') as f:
        f.write(template.format(propublica_header, twitter_config, handle, state,
                                include_rep))

    input("\nConfig file set up successfully. Press ENTER to {}".format(action))


if __name__ == '__main__':
    create_config()
