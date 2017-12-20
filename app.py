from get_data import get_rep, get_senators, Bill, Vote, get_api, get_url_len
from config import days_old_limit, max_tweet_len, include_rep
import datetime
import time
import json


url_len = get_url_len()
api = get_api()


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


def get_text(obj):
    member = obj.member
    if type(obj) == Bill:
        text = f"{member.name} introduced {obj}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 3] + '...'
    elif type(obj) == Vote:
        has_bill = type(obj.bill) == Bill
        text = f"{member.name} {obj}"
        max_text_len = max_tweet_len - 9 - len(obj.result) - url_len * has_bill
        if len(text) > max_text_len:
            text = text[:max_text_len - 3] + '...'
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


def update_status(item, text):
    """
    Posts the tweet
    """
    if type(item) == Bill:
        tweet = text + f'\n{item.govtrack_url}'
        api.update_status(tweet)
    elif type(item) == Vote:
        has_bill = type(item.bill) == Bill
        tweet = text + f'\nResult: {item.result}'
        if has_bill:
            tweet += f"\n{item.bill.govtrack_url}"
        api.update_status(tweet)


def get_data_and_tweet(member):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    member_tweets = 0
    data = [item for item in member.get_bills() + member.get_votes() if days_old(item) < days_old_limit]
    for item in data:
        tweets = [tweet[0] for tweet in get_history()]
        text = get_text(item)
        if text not in tweets:
            update_status(item, text)
            update_tweet_history(text)
            member_tweets += 1
    return member_tweets


def main():
    members = get_senators()
    if include_rep:
        from config import district
        members += get_rep(district)
    total_tweets = sum([get_data_and_tweet(member) for member in members])
    print(f"Done. Posted {total_tweets} new tweet{'s' * (total_tweets != 1)}.")


if __name__ == '__main__':
    main()
