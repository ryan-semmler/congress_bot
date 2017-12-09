# Congress Bot

Congress Bot is a twitter bot that tweets notifications whenever senators and/or congressmen from a given state introduce legislation or record a vote, including a description of the legislation and a link when available.


## Data
Data on individual senators' votes and sponsored bills comes from [Propublica's congress API](https://projects.propublica.org/api-docs/congress-api/)  
When the tweet regards a piece of legislation, a link to the legislation on [govtrack.us](https://www.govtrack.us/) will be included in the tweet.

## Requirements
Congress Bot relies on these python packages, which can be installed from pip:
* requests
* requests_oauthlib
* tweepy

## Setup
Requires API keys from Propublica and Twitter apps. The keys should be added to a config.py file. More information on formatting the config file can be found in config_template.py