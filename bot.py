from get_data import get_rep, get_senators, get_bills, get_votes
from secrets import twitter_config
from requests_oauthlib import OAuth1
import tweepy
import requests
import datetime
import time


"""
Steps:
-----------
1: establish member objects
2: search for bills
3: check bills against most_recent_bill to identify new ones
4: search for votes
5: check votes against most_recent_vote to ID new ones
6: tweet bills
7: tweet votes

optional:
---------
8: RT members' tweets
"""


def get_url_len():
    auth = OAuth1(twitter_config['consumer_key'],
                  twitter_config['consumer_secret'],
                  twitter_config['access_token'],
                  twitter_config['access_token_secret'])

    return requests.get('https://api.twitter.com/1.1/help/configuration.json', auth=auth).json()['short_url_length']


def get_api():
    auth = tweepy.OAuthHandler(twitter_config['consumer_key'], twitter_config['consumer_secret'])
    auth.set_access_token(twitter_config['access_token'], twitter_config['access_token_secret'])
    api = tweepy.API(auth)
    return api


def filter_data(member):
    """
    For now does NOT check against the most recent bill. Does other date check instead.
    Returns dict w/ keys 'bills' and 'votes'. values are lists.
    """
    bills = get_bills(member)
    votes = get_votes(member)
    date = time.localtime()
    now = datetime.datetime(date.tm_year, date.tm_month, date.tm_day)
    return {
        'bills': [bill for bill in bills if (bill.date - now).days < 2],
        'votes': [vote for vote in votes if (vote.date - now).days < 2]
    }
    # new_bills = []
    # for bill in bills:
    #     timedelta = bill.date - now
    #     delta = abs(timedelta.days)
    #     if delta < 2:
    #         new_bills.append(bill)
    # return new_bills


def tweet_bill(bill, api):
    member = bill.member
    url_len = get_url_len()
    text = f"{member.name} introduced {bill}"
    if len(text) > 140 - url_len - 1:
        text = text[:140 - url_len - 3] + '...'
    tweet = text + f'\n{bill.url}'
    api.update_status(tweet)


import pdb; pdb.set_trace()


def tweet_vote(vote):
    pass


def main():
    members = get_senators() + [get_rep()]
    for member in members:
        data = filter_data(member)
        bills = data['bills']
        for bill in bills:
            tweet_bill(bill)
        votes = data['votes']
        for vote in votes:
            tweet_vote(vote)
