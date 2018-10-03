try:
    from config import days_old_limit, handle, max_tweet_len, output_to_file, use_govtrack, tag_member
except ModuleNotFoundError:
    from create_config import create_config
    create_config(action='continue')
    from config import days_old_limit, handle, max_tweet_len, output_to_file, use_govtrack, tag_member

try:
    from tweet_history import history
except ModuleNotFoundError:
    history = {}

from get_data import get_members, Member, Bill, get_api, get_url_len
import pprint
import time


max_url_len = get_url_len()
api = get_api()
tweets = 0


def get_tweet_text(item):
    """Puts together the text of the tweet"""
    member = item.member
    member_name = member.name
    if tag_member and member.handle:
        member_name = '.@' + member.handle
    if isinstance(item, Bill):
        url = (item.url, item.govtrack_url)[use_govtrack]
        text = "{} {} {}".format(member_name, ('introduced', 'cosponsored')[item.cosponsored], item)
        url_len = min(max_url_len, len(url))
        if len(text) + url_len + 1 > max_tweet_len:
            text = text[:max_tweet_len - url_len - 3] + '…'
        tweet = text + '\n' + url
    else:  # if a Vote instance
        has_bill = isinstance(item.bill, Bill)
        text = "{} {}".format(member_name, item)
        if has_bill:
            url = (item.bill.url, item.bill.govtrack_url)[use_govtrack]
            url_len = min(max_url_len, len(url))
        else:
            url_len = 0
        max_text_len = max_tweet_len - (len(item.count) + len(item.result) + (url_len + 1) * has_bill + 2)
        if len(text) > max_text_len:
            text = text[:max_text_len - 2] + '…'
        tweet = text + "\n{} {}".format(item.result, item.count)
        if has_bill:
            tweet += "\n{}".format(url)
    return tweet


def get_data_and_tweet(member):  # , history, tweets):
    """Gets the member's votes and bills, tweets them if they haven't been tweeted already"""
    def item_in_history(item):
        """Determines whether the item has already been tweeted, returns bool"""
        if bill_id in history:
            date, obj_type, member = item.date, ('vote', 'bill')[is_bill], item.member.name
            for tweet in history['bill_id']:
                if tweet['date'] == date and tweet['type'] == obj_type and tweet['member'] == member:
                    return True
        return False

    def update_history(item, tweet_id):
        item_data = {'date': item.date,
                     'type': ('vote', 'bill')[is_bill],
                     'member': item.member.name,
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
            text = get_tweet_text(item)
            if bill_id in history:
                last_tweet = history[bill_id][-1]
                tweet = api.update_status(handle + ' ' + text, in_reply_to_status_id=last_tweet['tweet_id'])
            else:
                tweet = api.update_status(text)
            update_history(item, tweet.id_str)
            tweets += 1


def remove_old_tweets():
    for bill in history:
        last_tweet = [history[bill][-1]]
        if (Member.now - last_tweet).days > 365:
            last_tweet = []
        new_tweets = [tweet for tweet in history[bill][:-1] if (Member.now - tweet['date']).days <= days_old_limit]
        history[bill] = new_tweets + last_tweet
        if not history[bill]:
            del history[bill]


def main():
    for member in get_members():
        get_data_and_tweet(member)
    with open('tweet_history.py', 'w') as f:
        remove_old_tweets()
        f.write("import datetime\n\n\nhistory = {}".format(pprint.pformat(history, width=120)))
    if tweets and output_to_file:
        with open('tweet_log.txt', mode='a') as f:
            f.write("{} >> Posted {} new tweet{}.\n".format(time.ctime(), tweets, 's' * (tweets != 1)))
    print("Done. Posted {} new tweet{}.".format(tweets, 's' * (tweets != 1)))


if __name__ == '__main__':
    main()
