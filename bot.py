from get_data import get_rep, get_senators, get_bills, get_votes, Bill, Vote, Member, district
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
            'is_vote': False
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
            'is_vote': True
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


def get_tweets():
    """
    Creates Vote or Bill objects from dicts in cache
    """
    from secrets import cache
    return [(Bill, Vote)[item['data']['is_vote']](Member(item['member']), item['data']) for item in cache]


def days_old(item):
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    return (now - item.date).days


def initialize_tweet_cache(members):
    """
    Creates cache in secrets.py to include list of all votes and bills from the last two days.
    Objects in this cache will NOT get tweeted.
    """
    all_bills = sum([get_bills(member) for member in members], [])
    new_bills = [bill for bill in all_bills if days_old(bill) < 4]
    all_votes = sum([get_votes(member) for member in members], [])
    new_votes = [vote for vote in all_votes if days_old(vote) < 4]
    new_cache = [{'member': make_dict(item.member),
                  'data': make_dict(item)}
                 for item in new_bills + new_votes]
    with open('tweet_history.py', 'w') as f:
        f.write(new_cache)


def update_tweet_cache(tweet, cache):
    """
    Updates cache in secrets.py to include a new object that got tweeted out.
    'tweet' refers to Vote and Bill objects that have been tweeted.
    Older tweets removed from cache.
    """
    tweet_data = [{'member': make_dict(tweet.member), 'data': make_dict(tweet)}]
    print(tweet_data)
    with open('tweet_history.py', 'w') as f:
        f.write([item for item in cache if days_old(item) < 4] + tweet_data)


def update_status(item, api):
    """
    Tweets the thing
    """
    member = item.member
    if type(item) == Bill:
        url_len = get_url_len()
        text = f"{member.name} introduced {item}"
        if len(text) > 140 - url_len - 1:
            text = text[:140 - url_len - 3] + '...'
        tweet = text + f'\n{item.govtrack_url}'
        api.update_status(tweet)
    elif type(item) == Vote:
        tweet = f"{member.name} {item}"
        if len(tweet) > 140:
            tweet = tweet[:137] + '...'
        api.update_status(tweet)


def get_data_and_tweet(member, api):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = get_bills(member) + get_votes(member)
    tweets = get_tweets()
    for item in data:
        if item not in tweets and days_old(item) < 4:
            update_status(item, api)
            update_tweet_cache(item, cache)


def main():
    api = get_api()
    members = get_senators() + [get_rep()]
    initialize_tweet_cache(members)
    while True:
        for member in members:
            get_data_and_tweet(member, api)
        time.sleep(600)


if __name__ == '__main__':
    main()
