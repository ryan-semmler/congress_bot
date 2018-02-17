import tweepy
from config import twitter_config, handle, days_old_limit
import time
import datetime


def get_api():
    """
    Creates tweepy api object
    """
    auth = tweepy.OAuthHandler(twitter_config['consumer_key'], twitter_config['consumer_secret'])
    auth.set_access_token(twitter_config['access_token'], twitter_config['access_token_secret'])
    api = tweepy.API(auth)
    return api


api = get_api()


def delete_tweets(handle):
    total = 0
    date = time.localtime()
    now = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    while True:
        tweets = [post for post in api.user_timeline(handle) if (now - post.created_at.date()).days <= days_old_limit]
        total += len(tweets)
        if not tweets:
            break
        for tweet in tweets:
            api.destroy_status(tweet.id)
    print(f"Deleted {total} tweet{'s' * (total != 1)}")


if __name__ == '__main__':
    response = input(f"If you continue, all tweets from the last {days_old_limit} day{'s' * (days_old_limit != 1)} "
                     f"will be deleted. Continue? (y/N): ")
    if 'y' in response.lower():
        delete_tweets(handle)
    else:
        print("Cancelled. Did not delete tweets.")
