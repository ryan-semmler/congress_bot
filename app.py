try:
    from config import days_old_limit, max_tweet_len, include_rep
except:
    from create_config import create_config
    create_config(action='continue')
    from config import days_old_limit, max_tweet_len, include_rep


from get_data import get_rep, get_senators, Member, Bill, get_api, get_url_len
import pprint
import time


max_url_len = get_url_len()
api = get_api()


def get_tweet_text(item):
    """
    Puts together the text of the tweet
    """
    member = item.member
    if isinstance(item, Bill):
        text = "{} {} {}".format(member.name, ('introduced', 'cosponsored')[item.cosponsored], item)
        url_len = min(max_url_len, len(item.govtrack_url))
        if len(text) > max_tweet_len - url_len - 1:
            text = text[:max_tweet_len - url_len - 2] + '…'
        tweet = text + '\n{}'.format(item.govtrack_url)
    else:  # if a Vote instance
        has_bill = isinstance(item.bill, Bill)
        text = "{} {}".format(member.name, item)
        if has_bill:
            url_len = min(max_url_len, len(item.bill.govtrack_url))
        else:
            url_len = 0
        max_text_len = max_tweet_len - 2 - len(item.count) - len(item.result) - (url_len + 1) * has_bill
        if len(text) > max_text_len:
            text = text[:max_text_len - 2] + '…'
        tweet = text + "\n{} {}".format(item.result, item.count)
        if has_bill:
            tweet += "\n{}".format(item.bill.govtrack_url)
    return tweet


def get_data_and_tweet(member, history, tweets):
    """
    Gets the member's votes and bills, tweets them if they haven't been tweeted already
    """
    data = sorted([item for item in member.get_bills() + member.get_votes()], key=lambda x: x.date)
    for item in data:
        text = get_tweet_text(item)
        if text not in tweets:
            api.update_status(text)
            history.append((text, item.date))
    return history


def main():
    members = get_senators()
    if include_rep:
        members.append(get_rep())
    try:
        from tweet_history import history
    except:
        history = []
    old_tweets = len(history)
    tweets = [tweet[0] for tweet in history]
    for member in members:
        history = get_data_and_tweet(member, history, tweets)
    total_tweets = len(history) - old_tweets
    history = [item for item in history if (Member.now - item[1]).days <= days_old_limit]
    with open('tweet_history.py', 'w') as f:
        f.write("import datetime\n\n\nhistory = {}".format(pprint.pformat(history, width=110)))
    if total_tweets:
        with open('tweet_log.txt', mode='a') as f:
            f.write("{} >> Posted {} new tweet{}.".format(time.ctime(), total_tweets, 's' * (total_tweets != 1)))
    print("Done. Posted {} new tweet{}.".format(total_tweets, 's' * (total_tweets != 1)))


if __name__ == '__main__':
    main()
