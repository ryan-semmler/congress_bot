from config_template import template


input("This program will create the configuration file needed to run Congress Bot.\n"
      "Before continuing, make sure you've created a Twitter account and gotten an API key for that account.\n"
      "You'll need your API key for Twitter and Propublica to continue.\n\nPress ENTER to continue")


def clean(handle):
    return handle['@' in handle:]


handle = clean(input("Enter the bot's twitter handle: "))
state = input("Enter your state's two-letter abbreviation: ").lower()
district = input("Enter the number of the Congressional district used for the bot: ")
ppublica = input('Enter your Propublica API key: ')
consumer_key = input("There are four required keys for the Twitter API:"
                     "consumer key, consumer secret, access token, and access token secret\n"
                     "Enter the consumer key: ")
consumer_secret = input("Enter the consumer secret: ")
access_token = input("Enter the access token: ")
access_token_secret = input("Enter the access token secret: ")

twitter_config = {'consumer_key': consumer_key,
                  'consumer_secret': consumer_secret,
                  'access_token': access_token,
                  'access_token_secret': access_token_secret}

propublica_header = {'X-API-Key': ppublica}

with open("config.py", 'w') as f:
    f.write(template.format(propublica_header, twitter_config, handle, state, district))

input("\nConfig file set up successfully. Press ENTER to close")
