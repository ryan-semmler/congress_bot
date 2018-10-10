try:
    from config import tweet_age_limit, thread_age_limit, handle, max_tweet_len, output_to_file
except ModuleNotFoundError:
    from create_config import create_config
    create_config(action='continue')
    from config import tweet_age_limit, thread_age_limit, handle, max_tweet_len, output_to_file

try:
    from tweet_history import history
except (ModuleNotFoundError, ImportError):
    history = {}

from get_data import Bill, get_bill_by_id, get_members, get_api, get_url_len, now
from pprint import pformat


max_url_len = get_url_len()
api = get_api()
tweets = 0


def get_tweet_text(item, reply=False):
    """Puts together the text of the tweet"""
    member = item.member
    if isinstance(item, Bill):
        text = "{} {} {}".format(member.name, ('introduced', 'cosponsored')[item.cosponsored], item)
        url_len = min(max_url_len, len(item.url))
        if len(text) + url_len + 1 > max_tweet_len:
            text = text[:max_tweet_len - url_len - 3] + '…'
        tweet = text + '\n' + item.url
    else:  # if a Vote instance
        has_bill = isinstance(item.bill, Bill)
        text = "{} {}".format(member.name, item)
        if has_bill:
            url_len = min(max_url_len, len(item.bill.url))
        else:
            url_len = 0
        max_text_len = max_tweet_len - (len(item.count) + len(item.result) + (url_len + 1) * has_bill +
                                        (len(handle) + 1) * reply + 2)
        if len(text) > max_text_len:
            text = text[:max_text_len - 2] + '…'
        tweet = text + "\n{} {}".format(item.result, item.count)
        if has_bill:
            tweet += "\n{}".format(item.bill.url)
    return tweet


def get_data_and_tweet(member):
    """Gets the member's votes and bills, tweets them if they haven't been tweeted already"""

    def item_in_history(item):
        """Determines whether the item has already been tweeted, returns bool"""
        if bill_id in history:
            date, obj_type, member = item.date, ('vote', 'bill')[is_bill], item.member.last_name
            for tweet in history[bill_id]:
                if tweet['item_date'] == date and tweet['type'] == obj_type and tweet['member'] == member:
                    return True
        return False

    def update_history(item, tweet_id):
        """Adds new tweet to history"""
        item_data = {'item_date': item.date,
                     'tweeted_date': now,
                     'type': ('vote', 'bill')[is_bill],
                     'member': item.member.last_name,
                     'tweet_id': tweet_id}
        if bill_id in history:
            history[bill_id].append(item_data)
        else:
            history[bill_id] = [item_data]

    data = sorted(member.get_bills() + member.get_votes(), key=lambda x: x.date)
    for item in data:
        is_bill = isinstance(item, Bill)
        if is_bill:
            bill_id = item.id
        else:  # if a Vote instance
            if isinstance(item.bill, Bill):
                bill_id = item.bill.id
            else:
                bill_id = item.bill['bill_id']
        if not item_in_history(item):
            if bill_id in history:
                text = get_tweet_text(item, reply=True)
                last_tweet = history[bill_id][-1]
                tweet = api.update_status(handle + ' ' + text, in_reply_to_status_id=last_tweet['tweet_id'])
            else:
                text = get_tweet_text(item)
                tweet = api.update_status(text)
            update_history(item, tweet.id_str)
            global tweets
            tweets += 1


def enacted_or_vetoed():
    """Tweets reply to bill's tweet thread when it's enacted or vetoed"""
    for bill_id in history:
        bill = get_bill_by_id(bill_id)
        if bill:
            last_tweet = history[bill_id][-1]
            if bill.enacted:
                text = "{} has been enacted.\n{}".format(bill.number, bill.url)
                api.update_status(handle + ' ' + text, in_reply_to_status_id=last_tweet['tweet_id'])
                history[bill_id] = []
            elif bill.vetoed:
                item_in_history = any(tweet['type'] == 'veto' for tweet in history[bill_id])
                if not item_in_history:
                    text = "{} has been vetoed.\n{}".format(bill.number, bill.url)
                    tweet = api.udpate_status(handle + ' ' + text, in_reply_to_status_id=last_tweet['tweet_id'])
                    item_data = {'item_date': bill.date,
                                 'tweeted_date': now,
                                 'type': 'veto',
                                 'member': 'none',
                                 'tweet_id': tweet.id_str}
                    history[bill_id].append(item_data)


def remove_old_tweets():
    """Removes old items from history"""
    for bill_id in history:
        last_tweet = [history[bill_id][-1]]
        if (now - last_tweet[0]['tweeted_date']).days > thread_age_limit:
            last_tweet = []
        new_tweets = [tweet for tweet in history[bill_id][:-1] if (now - tweet['tweeted_date']).days <= tweet_age_limit]
        history[bill_id] = new_tweets + last_tweet
    return {k: v for k, v in history.items() if history[k]}


def main():
    enacted_or_vetoed()
    for member in get_members():
        get_data_and_tweet(member)
    history = remove_old_tweets()
    with open('tweet_history.py', mode='w') as f:
        f.write("import datetime\n\n\nhistory = {}\n".format(pformat(history)))
    if tweets and output_to_file:
        with open('tweet_log.txt', mode='a') as f:
            import time
            f.write("{} >> Posted {} new tweet{}.\n".format(time.ctime(), tweets, 's' * (tweets != 1)))
    print("Done. Posted {} new tweet{}.".format(tweets, 's' * (tweets != 1)))


if __name__ == '__main__':
    main()
