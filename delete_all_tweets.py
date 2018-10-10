from get_data import get_api
from config import handle, tweet_age_limit
from tweet_history import history
import time
import datetime
import pprint


def delete_tweets(history):
    total = 0
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    api = get_api()
    tweets = [post for post in api.user_timeline(handle) if (now - post.created_at.date()).days <= tweet_age_limit]
    while tweets:
        total += len(tweets)
        for tweet in tweets:
            api.destroy_status(tweet.id)
        tweets = [post for post in api.user_timeline(handle) if (now - post.created_at.date()).days <= tweet_age_limit]
    for bill_id in history:
        history[bill_id] = [item for item in history[bill_id] if (now - item['tweeted_date']).days > tweet_age_limit]
    history = {k: v for k, v in history.items() if history[k]}
    with open('tweet_history.py', 'w') as f:
        f.write("import datetime\n\n\nhistory = {}\n".format(pprint.pformat(history)))
    print("Deleted {} tweet{}.".format(total, 's' * (total != 1)))


if __name__ == '__main__':
    response = input("If you continue, all tweets from the last {} day{} will be deleted. Continue? (y/N): ".format(
                     tweet_age_limit, 's' * (tweet_age_limit != 1)))
    if 'y' in response.lower():
        delete_tweets(history)
    else:
        print("Cancelled. Did not delete tweets.")
