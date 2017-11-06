from get_data import Member, Bill, Vote

geocodio_key = 'ff990b400520cd6c0f905cac5060b650a9abcc5'
propublica_header = {'X-API-Key': '5DmmhsiQ6SLlkL7FMRwJPgZnhmAraCY85NU4WvW1'}

# "consumer_key" is the API key. "Consumer_secret" is the API secret.
twitter_config = {'consumer_key': 'YTFDAFqgujba7oFfLz7Bsxl0p', 'consumer_secret': 'RZeeznpnP6C7JvojuP1qL7KASkP0xlQk1lQAygpCcOz7Bp7ssE', 'access_token': '926572112902590465-atYiy6HSCTxI9x2S4ctkUa3Hn7oVDjM', 'access_token_secret': 'QmUtIv82lnvEL7mJzSZvEfeRNMEqOcWPYCivCASLmfGqA'}

lat = 35.95115
lon = -78.54433

cache = [{'class': <class 'get_data.Bill'>, 'member': {'id': 'T000476', 'first_name': 'Thom', 'last_name': 'Tillis', 'role': 'senator', 'district': 2, 'party': 'R', 'twitter_id': 'senthomtillis', 'next_election': '2020'}, 'data': {'number': 'S.2030', 'bill_id': 's2030-115', 'title': 'A bill to deem the compliance date for amended energy conservation standards for ceiling light kits to be January 21, 2020, and for other purposes.', 'short_title': 'Ceiling Fan Energy Conservation Harmonization Act', 'congressdotgov_url': 'https://www.congress.gov/bill/115th-congress/senate-bill/2030', 'govtrack_url': 'https://www.govtrack.us/congress/bills/115/s2030', 'introduced_date': '2017-10-30', 'primary_subject': 'Energy'}}]
