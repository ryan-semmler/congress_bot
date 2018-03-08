from get_data import get_rep, get_senators, Bill, Vote, get_api, get_url_len
from config import days_old_limit, max_tweet_len, include_rep
import datetime
import time
import pprint


url_len = get_url_len()
api = get_api()
date = time.localtime()
now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)


def get_tweet_text(item):
    """
    Puts together the text of the tweet
    """
    member = item.member
    if isinstance(item, Bill):
        text = f"{member.name} {('introduced', 'cosponsored')[item.cosponsored]} {item}"
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 4] + '...'
        tweet = text + f'\n{item.govtrack_url}'
    elif isinstance(item, Vote):
        has_bill = isinstance(item.bill, Bill)
        text = f"{member.name} {item}"
        max_text_len = max_tweet_len - 2 - len(item.count) - len(item.result) - (url_len + 1) * has_bill
        if len(text) > max_text_len:
            text = text[:max_text_len - 4] + '...'
        tweet = text + f"\n{item.result} {item.count}"
        if has_bill:
            tweet += f"\n{item.bill.govtrack_url}"
    return tweet


def get_data_and_tweet(member, history, tweets):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = sorted([item for item in member.get_bills(now) + member.get_votes(now)], key=lambda x: x.date)
    for item in data:
        text = get_tweet_text(item)
        if text not in tweets:
            api.update_status(text)
            history.append((text, item.date))
    return history


def main():
    members = get_senators()
    if include_rep:
        members += get_rep()
    try:
        from tweet_history import history
    except ModuleNotFoundError:
        history = []
    old_tweets = len(history)
    tweets = [tweet[0] for tweet in history]
    for member in members:
        history = get_data_and_tweet(member, history, tweets)
    total_tweets = len(history) - old_tweets
    history = [item for item in history if (now - item[1]).days <= days_old_limit]
    with open('tweet_history.py', 'w') as f:
        f.write(f"import datetime\n\n\nhistory = {pprint.pformat(history, width=110)}")
    print(f"Done. Posted {total_tweets} new tweet{'s' * (total_tweets != 1)}.")


if __name__ == '__main__':
    main()
