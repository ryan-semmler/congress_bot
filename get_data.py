import requests
from config import state, propublica_header, twitter_config
import datetime
import tweepy
from requests_oauthlib import OAuth1
import pdb


class Member:
    def __init__(self, data):
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.name = ' '.join((data['first_name'], data['last_name']))
        if 'senator' in data['role'].lower():
            self.chamber = 'Senate'
            self.title = 'Senator'
        else:
            self.chamber = "House"
            self.district = data['district']
            self.title = 'Representative'
        self.state = state.upper()
        self.party = data['party']
        self.handle = data['twitter_id']
        self.next_election = data['next_election']

    def __repr__(self):
        dist = ''
        if hasattr(self, 'district'):
            dist += f' District {self.district}'
        return f"{self.title} {self.first_name} {self.last_name}, {self.state}{dist}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.name == other.name

    def get_votes(self):
        vote_data = requests.get(f"https://api.propublica.org/congress/v1/members/{self.id}/votes.json",
                                 headers=propublica_header).json()['results'][0]['votes']
        all_votes = [Vote(self, data) for data in vote_data]
        return [vote for vote in all_votes if vote.include][::-1]

    def get_bills(self):
        bill_data = requests.get(f"https://api.propublica.org/congress/v1/members/{self.id}/bills/"
                                 "introduced.json", headers=propublica_header).json()['results'][0]['bills']
        bills = [Bill(self, data) for data in bill_data]

        cosponsored_bill_data = requests.get(
            f"https://api.propublica.org/congress/v1/members/{self.id}/bills/cosponsored.json",
            headers=propublica_header).json()['results'][0]['bills']
        cosponsored_bills = [Bill(self, data, cosponsored=True) for data in cosponsored_bill_data]
        return sorted(bills + cosponsored_bills, key=lambda x: x.date)


class Bill:
    def __init__(self, member, data, cosponsored=False):
        self.member = member
        self.number = data['number']
        self.id = data['bill_id']
        self.title = data['title']
        self.short_title = data['short_title']
        self.url = data['congressdotgov_url']
        self.govtrack_url = data['govtrack_url']
        year, month, day = [int(thing) for thing in data['introduced_date'].split('-')]
        self.date = datetime.date(year, month, day)
        self.subject = data['primary_subject']
        self.cosponsored = cosponsored

    def __repr__(self):
        return f"{self.number}: {self.short_title}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if type(other) != Bill:
            return False
        return all((self.id == other.id, self.date == other.date))


class Vote:
    def __init__(self, member, data):
        self.member = member
        self.session = data['session']
        try:
            self.bill = self.get_bill_by_id(member, data['bill']['bill_id'])
        except:
            self.bill = data['bill']
        self.description = data['description']
        self.question = data['question']
        self.result = data['result']
        year, month, day = [int(thing) for thing in data['date'].split('-')]
        self.date = datetime.date(year, month, day)
        self.position = data['position'].lower()
        self.for_passage = 'pass' in self.question.lower()
        self.include = any([word in self.question.lower() for word in ("pass", "agree", "nomination", "resolution")])

    def __repr__(self):
        connector = ' '
        if 'to' not in self.description[:2].lower():
            connector += 'on '
        if 'Act' in self.description.split(',')[0]:
            connector += 'the '
        if 'not' in self.position:
            return f"did not vote{connector}{self.description}."
        return f"voted {self.position}{connector}{self.description}."

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if type(other) != Vote:
            return False
        return all((self.member == other.member, self.bill == other.bill))

    def get_bill_by_id(self, member, id):
        bill_id, congress = id.split('-')
        bill_data = requests.get(f"https://api.propublica.org/congress/v1/{congress}/bills/{bill_id}.json",
                                 headers=propublica_header).json()['results'][0]
        return Bill(member, bill_data)


# find congresspeople
def get_rep(district):
    rep_data = requests.get(f"https://api.propublica.org/congress/v1/members/house/{state}/{district}/current.json",
                            headers=propublica_header).json()['results'][0]
    return [Member(rep_data)]


def get_senators():
    senators_data = requests.get(f"https://api.propublica.org/congress/v1/members/senate/{state}/current.json",
                                 headers=propublica_header).json()['results']
    return [Member(data) for data in senators_data]


def get_api():
    auth = tweepy.OAuthHandler(twitter_config['consumer_key'], twitter_config['consumer_secret'])
    auth.set_access_token(twitter_config['access_token'], twitter_config['access_token_secret'])
    return tweepy.API(auth)


def get_url_len():
    auth = OAuth1(twitter_config['consumer_key'],
                  twitter_config['consumer_secret'],
                  twitter_config['access_token'],
                  twitter_config['access_token_secret'])
    return requests.get('https://api.twitter.com/1.1/help/configuration.json', auth=auth).json()['short_url_length']


if __name__ == '__main__':
    senators = get_senators()
    thom = senators[0]
    bills = thom.get_bills()
    bill = thom.get_bills()[0]
    votes = thom.get_votes()
    vote = thom.get_votes()[0]
    from app import days_old

    pdb.set_trace()
