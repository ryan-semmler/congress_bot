from get_data import get_rep, get_senators, Bill, Vote, get_api, get_url_len
from config import days_old_limit, max_tweet_len, include_rep
import datetime
import time
import pprint


url_len = get_url_len()
api = get_api()

# TODO combine text-adding features of get_text and update_status
# TODO debug get_text allowing tweets too long for api
# TODO straighten out var names. is 'obj' same as 'item'?
# TODO work out which tweets should be allowed through. Which votes should be excluded?


def days_old(item):
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    try:
        return (now - item.date).days
    except AttributeError:
        return (now - item).days


def get_text(obj):
    member = obj.member
    if isinstance(obj, Bill):
        text = f"{member.name} {('introduced', 'cosponsored')[obj.cosponsored]} {obj}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 3] + '...'
    elif isinstance(obj, Vote):
        has_bill = isinstance(obj.bill, Bill)
        text = f"{member.name} {obj}"
        max_text_len = max_tweet_len - 9 - len(obj.result) - url_len * has_bill
        if len(text) > max_text_len:
            text = text[:max_text_len - 3] + '...'
    return text


def update_status(item, text):
    """
    Posts the tweet
    """
    if isinstance(item, Bill):
        tweet = text + f'\n{item.govtrack_url}'
    elif isinstance(item, Vote):
        has_bill = isinstance(item.bill, Bill)
        tweet = text + f'\nResult: {item.result}'
        if has_bill:
            tweet += f"\n{item.bill.govtrack_url}"
        print(tweet, len(tweet))
    api.update_status(tweet)


def get_data_and_tweet(member, history, tweets):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = [item for item in member.get_bills() + member.get_votes() if days_old(item) <= days_old_limit]
    for item in data:
        text = get_text(item)
        if text not in tweets:
            update_status(item, text)
            history.append((text, item.date))
    return history


def main():
    members = get_senators()
    if include_rep:
        members += get_rep()
    try:
        from tweet_history import history
    except:
        history = []
    old_tweets = len(history)
    tweets = [tweet[0] for tweet in history]
    for member in members:
        history = get_data_and_tweet(member, history, tweets)
    total_tweets = len(history) - old_tweets
    history = [item for item in history if days_old(item[1]) <= days_old_limit]
    with open('tweet_history.py', 'w') as f:
        f.write(f"import datetime\n\n\nhistory = {pprint.pformat(history, width=110)}")
    print(f"Done. Posted {total_tweets} new tweet{'s' * (total_tweets != 1)}.")


if __name__ == '__main__':
    main()
