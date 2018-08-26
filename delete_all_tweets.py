from get_data import get_api
from config import handle, days_old_limit
import time
import datetime


def delete_tweets():
    total = 0
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    api = get_api()
    while True:
        tweets = [post for post in api.user_timeline(handle) if (now - post.created_at.date()).days <= days_old_limit]
        total += len(tweets)
        if not tweets:
            break
        for tweet in tweets:
            api.destroy_status(tweet.id)
    with open('tweet_history.py', 'w') as f:
        f.write("import datetime\n\n\nhistory = []")
    print("Deleted {} tweet{}".format(total, 's' * (total != 1)))


if __name__ == '__main__':
    response = input("If you continue, all tweets from the last {} day{} "
                     "will be deleted. Continue? (y/N): ").format(days_old_limit, 's' * days_old_limit != 1)
    if 'y' in response.lower():
        delete_tweets()
    else:
        print("Cancelled. Did not delete tweets.")
