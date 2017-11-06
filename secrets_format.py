# Maybe reintegrate this into secrets.py
# will probably have to expend twitter_config to include the keys, with "" values.

template = """from get_data import Member, Bill, Vote

geocodio_key = '{}'
propublica_header = {}

# "consumer_key" is the API key. "Consumer_secret" is the API secret.
twitter_config = {}

lat = {}
lon = {}

cache = {}
"""
