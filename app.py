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


# def make_dict(item):
#     """
#     Item is a Vote or Bill
#     returns dict of item data in format usable by Vote and Bill inits
#     """
#     if type(item) == Bill:
#         return {
#             'number': item.number,
#             'bill_id': item.id,
#             'title': item.title,
#             'short_title': item.short_title,
#             'congressdotgov_url': item.url,
#             'govtrack_url': item.govtrack_url,
#             'introduced_date': '-'.join([str(thing) for thing in (item.date.year, item.date.month, item.date.day)]),
#             'primary_subject': item.subject,
#             'is_vote': 0
#         }
#     elif type(item) == Vote:
#         return {
#             'session': item.session,
#             'bill': item.bill if type(item.bill) == dict else make_dict(item.bill),
#             'description': item.description,
#             'question': item.question,
#             'result': item.result,
#             'date': '-'.join([str(thing) for thing in (item.date.year, item.date.month, item.date.day)]),
#             'position': item.position,
#             'is_vote': 1
#         }
#     elif type(item) == Member:
#         return {
#             'id': item.id,
#             'first_name': item.first_name,
#             'last_name': item.last_name,
#             'role': '' + 'senator' * (item.title == 'Senator'),
#             'district': district,
#             'party': item.party,
#             'twitter_id': item.handle,
#             'next_election': item.next_election
#         }


# def make_object(item):
#     """
#     Converts data from tweet_history to Vote or Bill object
#     """
#     return (Bill, Vote)[item['data']['is_vote']](Member(item['member']), item['data'])


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
    return (now - item).days


# def initialize_tweet_cache(members):
#     """
#     Creates cache in config.py to include list of all votes and bills from the last two days.
#     Objects in this cache will NOT get tweeted.
#     """
#     all_bills = sum([get_bills(member) for member in members], [])
#     new_bills = [bill for bill in all_bills if days_old(bill) < days_old_limit]
#     all_votes = sum([get_votes(member) for member in members], [])
#     new_votes = [vote for vote in all_votes if days_old(vote) < days_old_limit]
#     new_cache = [{'member': make_dict(item.member),
#                   'data': make_dict(item)}
#                  for item in new_bills + new_votes]
#     with open('tweet_history.json', 'w') as f:
#         json.dump({"data": new_cache}, f)


def get_text(obj):
    member = obj.member
    url_len = get_url_len()
    if type(obj) == Bill:
        text = f"{member.name} introduced {obj}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 3] + '...'
    elif type(obj) == Vote:
        has_bill = type(obj.bill) == Bill
        text = f"{member.name} {obj}"
        if len(text) > max_tweet_len - url_len * has_bill:
            text = text[:max_tweet_len - url_len * has_bill - 3] + '...'
    return text


def update_tweet_history(tweet_text):
    """
    Updates cache in config.py to include a new object that got tweeted out.
    'tweet' refers to Vote and Bill objects that have been tweeted.
    Older tweets removed from cache.
    """
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    tweet_data = (tweet_text, now)
    with open('tweet_history.json', 'r') as f:
        history = json.load(f)
    if history:
        combined = [item for item in history['data'] if days_old(item[1]) <= days_old_limit] + [tweet_data]
    else:
        combined = tweet_data
    with open('tweet_history.json', 'w') as f:
        json.dump({"data": combined}, f, indent=2)


def update_status(item, api):
    """
    Posts the tweet
    """
    text = get_text(item)
    if type(item) == Bill:
        tweet = text + f'\n{item.govtrack_url}'
        api.update_status(tweet)
    elif type(item) == Vote:
        has_bill = type(item.bill) == Bill
        tweet = text
        if has_bill:
            tweet += f"\n{item.bill.govtrack_url}"
        api.update_status(tweet)


def get_data_and_tweet(member, api):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = [item for item in get_bills(member) + get_votes(member) if days_old(item) < days_old_limit]
    for item in data:
        tweets = [tweet[0] for tweet in get_history()]
        if get_text(item) not in tweets:
            update_status(item, api)
            update_tweet_history(get_text(item))


def main():
    api = get_api()
    members = get_senators() + get_rep() * include_rep
    # initialize_tweet_cache(members)
    # while True:
    for member in members:
        get_data_and_tweet(member, api)


if __name__ == '__main__':
    main()
