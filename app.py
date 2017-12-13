from get_data import get_rep, get_senators, get_bills, get_votes, Bill, Vote, Member, district
from config import twitter_config
from requests_oauthlib import OAuth1
import tweepy
import requests
import datetime
import time
import json


days_old_limit = 4
max_tweet_len = 280
include_rep = True


def get_url_len():
    """
    Twitter shortens urls to a specific length, which varies by day. Function returns url length
    """
    auth = OAuth1(twitter_config['consumer_key'],
                  twitter_config['consumer_secret'],
                  twitter_config['access_token'],
                  twitter_config['access_token_secret'])

    return requests.get('https://api.twitter.com/1.1/help/configuration.json', auth=auth).json()['short_url_length']


def get_api():
    """
    Creates tweepy api object
    """
    auth = tweepy.OAuthHandler(twitter_config['consumer_key'], twitter_config['consumer_secret'])
    auth.set_access_token(twitter_config['access_token'], twitter_config['access_token_secret'])
    api = tweepy.API(auth)
    return api


def get_history():
    """
    Creates Vote or Bill objects from dicts in cache
    """
    with open("tweet_history.json", "r") as f:
        history = json.load(f)
    return history['data']


def days_old(item):
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    if type(item) in (Vote, Bill):
        return (now - item.date).days
    return (now - datetime.date(item[0], item[1], item[2])).days


def get_text(obj, url_len):
    member = obj.member
    if type(obj) == Bill:
        text = f"{member.name} introduced {obj}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 3] + '...'
    elif type(obj) == Vote:
        has_bill = type(obj.bill) == Bill
        text = f"{member.name} {obj}"
        if len(text) > max_tweet_len - url_len * has_bill:
            text = text[:max_tweet_len - url_len * has_bill - len(obj.result) - 4] + '...'
    return text


def update_tweet_history(tweet_text):
    """
    Updates cache in config.py to include a new object that got tweeted out.
    'tweet' refers to Vote and Bill objects that have been tweeted.
    Older tweets removed from cache.
    """
    date = time.localtime()
    now = (date.tm_year, date.tm_mon, date.tm_mday)
    tweet_data = (tweet_text, now)
    with open('tweet_history.json', 'r') as f:
        history = json.load(f)
    if history:
        combined = [item for item in history['data'] if days_old(item[1]) <= days_old_limit] + [tweet_data]
    else:
        combined = tweet_data
    with open('tweet_history.json', 'w') as f:
        json.dump({"data": combined}, f, indent=2)


def update_status(item, api, url_len):
    """
    Posts the tweet
    """
    text = get_text(item, url_len)
    if type(item) == Bill:
        tweet = text + f'\n{item.govtrack_url}'
        api.update_status(tweet)
    elif type(item) == Vote:
        has_bill = type(item.bill) == Bill
        tweet = text + f'\n{item.result}'
        if has_bill:
            tweet += f"\n{item.bill.govtrack_url}"
        api.update_status(tweet)


def get_data_and_tweet(member, api, url_len):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    member_tweets = 0
    data = [item for item in get_bills(member) + get_votes(member) if days_old(item) < days_old_limit]
    for item in data:
        tweets = [tweet[0] for tweet in get_history()]
        if get_text(item, url_len) not in tweets:
            update_status(item, api, url_len)
            update_tweet_history(get_text(item, url_len))
            member_tweets += 1
    return member_tweets


def main():
    url_len = get_url_len()
    api = get_api()
    members = get_senators()
    if include_rep:
        members += get_rep()
    # initialize_tweet_cache(members)
    # while True:
    total_tweets = 0
    for member in members:
        total_tweets += get_data_and_tweet(member, api, url_len)
    print(f"Done. Posted {total_tweets} new tweet{'s' * (total_tweets != 1)}.")


if __name__ == '__main__':
    main()
