from get_data import get_rep, get_senators, get_bills, get_votes, Bill, Vote, Member, district
from config import twitter_config
from requests_oauthlib import OAuth1
import tweepy
import requests
import datetime
import time
import json
from pprint import pprint


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

days_old_limit = 4
max_tweet_len = 280


def get_url_len():
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


def make_dict(item):
    """
    Item is a Vote or Bill
    returns dict of item data in format usable by Vote and Bill inits
    """
    if type(item) == Bill:
        return {
            'number': item.number,
            'bill_id': item.id,
            'title': item.title,
            'short_title': item.short_title,
            'congressdotgov_url': item.url,
            'govtrack_url': item.govtrack_url,
            'introduced_date': '-'.join([str(thing) for thing in (item.date.year, item.date.month, item.date.day)]),
            'primary_subject': item.subject,
            'is_vote': 0
        }
    elif type(item) == Vote:
        return {
            'session': item.session,
            'bill': item.bill,
            'description': item.description,
            'question': item.question,
            'result': item.result,
            'date': '-'.join([str(thing) for thing in (item.date.year, item.date.month, item.date.day)]),
            'position': item.position,
            'is_vote': 1
        }
    elif type(item) == Member:
        return {
            'id': item.id,
            'first_name': item.first_name,
            'last_name': item.last_name,
            'role': '' + 'senator' * (item.title == 'Senator'),
            'district': district,
            'party': item.party,
            'twitter_id': item.handle,
            'next_election': item.next_election
        }


def make_object(item):
    """
    Converts data from tweet_history to Vote or Bill object
    """
    return (Bill, Vote)[item['data']['is_vote']](Member(item['member']), item['data'])


def get_history():
    """
    Creates Vote or Bill objects from dicts in cache
    """
    with open("tweet_history.json", "r") as f:
        history = json.load(f)
    if history:
        return [make_object(item) for item in history['data']]
    return []


def days_old(item):
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    return (now - item.date).days


def initialize_tweet_cache(members):
    """
    Creates cache in config.py to include list of all votes and bills from the last two days.
    Objects in this cache will NOT get tweeted.
    """
    all_bills = sum([get_bills(member) for member in members], [])
    new_bills = [bill for bill in all_bills if days_old(bill) < days_old_limit]
    all_votes = sum([get_votes(member) for member in members], [])
    new_votes = [vote for vote in all_votes if days_old(vote) < days_old_limit]
    new_cache = [{'member': make_dict(item.member),
                  'data': make_dict(item)}
                 for item in new_bills + new_votes]
    with open('tweet_history.json', 'w') as f:
        json.dump({"data": new_cache}, f)
        # f.write(f"history = {new_cache}")


def update_tweet_history(tweet):
    """
    Updates cache in config.py to include a new object that got tweeted out.
    'tweet' refers to Vote and Bill objects that have been tweeted.
    Older tweets removed from cache.
    """
    tweet_data = [{'member': make_dict(tweet.member), 'data': make_dict(tweet)}]
    with open('tweet_history.json', 'r') as f:
        history = json.load(f)
    if history:
        combined = history['data'] + tweet_data
    else:
        combined = tweet_data
    with open('tweet_history.json', 'w') as f:
        json.dump({"data": combined}, f)
        # f.write(json.dumps({"data": combined}))


def update_status(item, api):
    """
    Tweets the thing
    """
    member = item.member
    if type(item) == Bill:
        url_len = get_url_len()
        text = f"{member.name} introduced {item}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 3] + '...'
        tweet = text + f'\n{item.govtrack_url}'
        api.update_status(tweet)
    elif type(item) == Vote:
        tweet = f"{member.name} {item}"
        if len(tweet) > max_tweet_len:
            tweet = tweet[:max_tweet_len - 3] + '...'
        api.update_status(tweet)


def get_data_and_tweet(member, api):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = [item for item in get_bills(member) + get_votes(member) if days_old(item) < days_old_limit]
    for item in data:
        tweets = get_history()
        if item not in tweets:
            update_status(item, api)
            update_tweet_history(item)


def main():
    api = get_api()
    members = get_senators() + get_rep()
    # initialize_tweet_cache(members)
    while True:
        for member in members:
            get_data_and_tweet(member, api)
        input("Press ENTER to continue")
        print("\n\n----------------------\n    Looping again\n----------------------\n")


if __name__ == '__main__':
    main()
