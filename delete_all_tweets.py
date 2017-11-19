import tweepy
from config import twitter_config, handle


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
    while True:
        tweets = api.user_timeline(handle)
        total += len(tweets)
        if not tweets:
            break
        for tweet in tweets:
            api.destroy_status(tweet.id)
    print(f"Deleted {total} tweet" + "s" * (total != 1))


if __name__ == '__main__':
    delete_tweets(handle)
