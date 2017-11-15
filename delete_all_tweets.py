import tweepy
from secrets import twitter_config, handle


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
    while True:
        tweets = api.user_timeline(handle)
        if not tweets:
            break
        tweet_ids = [tweet.id for tweet in tweets]
        for id in tweet_ids:
            api.destroy_status(id)


delete_tweets(handle)
