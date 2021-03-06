from requests import get
from config import (state, include_rep, propublica_header, twitter_config,
                    district, tweet_age_limit, use_govtrack, tag_member)
from datetime import date
from time import localtime
from tweepy import OAuthHandler, API
from requests_oauthlib import OAuth1


ltime = localtime()
now = date(ltime.tm_year, ltime.tm_mon, ltime.tm_mday)


class Member:
    def __init__(self, data):
        self.id = data['id']
        self.handle = data['twitter_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        if tag_member and self.handle:
            self.name = '@' + self.handle
        else:
            self.name = data['first_name'] + ' ' + data['last_name']
        if 'senator' in data['role'].lower():
            self.chamber = 'Senate'
            self.title = 'Senator'
        else:
            self.chamber = "House"
            self.district = data['district']
            self.title = 'Representative'
        self.state = state.upper()
        self.party = data['party']
        self.next_election = data['next_election']

    def __repr__(self):
        dist = ''
        if hasattr(self, 'district'):
            dist += str(self.district)
        return "{} {} {} ({}-{}{})".format(self.title, self.first_name, self.last_name, self.party, self.state, dist)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.name == other.name

    def get_votes(self):
        """returns list of bills and nominations voted on by the member"""
        vote_data = get("https://api.propublica.org/congress/v1/members/{}/votes.json".format(self.id),
                                 headers=propublica_header).json()['results'][0]['votes']
        all_votes = [Vote(self, data) for data in vote_data]
        recent_votes = [vote for vote in all_votes if (now - vote.date).days <= tweet_age_limit]
        return [vote for vote in recent_votes if vote.include]

    def get_bills(self):
        """returns list of bills introduced or cosponsored by the member"""
        bill_data = get("https://api.propublica.org/congress/v1/members/{}/bills/introduced.json".format(
            self.id), headers=propublica_header).json()['results'][0]['bills']
        bills = [Bill(self, data) for data in bill_data]

        cosponsored_bill_data = get(
            "https://api.propublica.org/congress/v1/members/{}/bills/cosponsored.json".format(self.id),
            headers=propublica_header).json()['results'][0]['bills']
        cosponsored_bills = [Bill(self, data, cosponsored=True) for data in cosponsored_bill_data]
        return [bill for bill in bills + cosponsored_bills if (now - bill.date).days <= tweet_age_limit]


class Bill:
    def __init__(self, member, data, cosponsored=False):
        self.member = member
        self.number = data['number']
        self.id = data['bill_id']
        self.title = data['title']
        self.short_title = data['short_title']
        self.url = (data['congressdotgov_url'], data['govtrack_url'])[use_govtrack]
        self.date = date(*map(int, data['introduced_date'].split('-')))
        self.subject = data['primary_subject']
        self.cosponsored = cosponsored
        self.vetoed = data['vetoed']
        self.enacted = data['enacted']

    def __repr__(self):
        return "{}: {}".format(self.number, self.short_title)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if type(other) != Bill:
            return False
        return self.id == other.id and self.date == other.date


class Vote:
    def __init__(self, member, data):
        self.member = member
        self.session = data['session']
        self.bill = get_bill_by_id(data['bill']['bill_id'], member) or data['bill']
        self.description = data['description']
        self.question = data['question']
        self.result = data['result']
        self.count = "{}-{}".format(data['total']['yes'], data['total']['no'])
        self.date = date(*map(int, data['date'].split('-')))
        self.position = data['position'].lower()
        self.for_passage = 'pass' in self.question.lower()
        valid_question = not any([word in self.question.lower() for word in ("amendment", "recommit", "table appeal",
                                                                             "previous question", "motion", "journal",
                                                                             "conference")])
        valid_desc = "providing for consideration" not in self.description.lower()
        self.include = valid_question and valid_desc

    def __repr__(self):
        connector = ' '
        if 'to' not in self.description[:2].lower():
            connector += 'on '
            if 'Act' in self.description.split(',')[0]:
                connector += 'the '
            elif 'nomination' not in self.question.lower():
                self.description = self.description[:1].lower() + self.description[1:]
        if 'not' in self.position:
            return "did not vote{}{}{}".format(connector, self.description, '.' * (not self.description.endswith('.')))
        return "voted {}{}{}{}".format(self.position, connector, self.description,
                                       '.' * (not self.description.endswith('.')))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if type(other) != Vote:
            return False
        return self.member == other.member and self.bill == other.bill


def get_bill_by_id(bill_id, member=None):
    bill_number, congress = bill_id.split('-')
    try:
        bill_data = get("https://api.propublica.org/congress/v1/{}/bills/{}.json".format(congress, bill_number),
                                 headers=propublica_header).json()['results'][0]
        return Bill(member, bill_data)
    except KeyError:
        return None


def get_members():
    """Return Member instances for senators and representative if applicable"""
    senators_data = get("https://api.propublica.org/congress/v1/members/senate/{}/current.json".format(state),
                                 headers=propublica_header).json()['results']
    senators = [Member(data) for data in senators_data]
    if include_rep and district:
        rep_data = get("https://api.propublica.org/congress/v1/members/house/{}/{}/current.json".format(
                                state, district), headers=propublica_header).json()['results'][0]
        return senators + [Member(rep_data)]
    return senators


def get_api():
    auth = OAuthHandler(twitter_config['consumer_key'], twitter_config['consumer_secret'])
    auth.set_access_token(twitter_config['access_token'], twitter_config['access_token_secret'])
    return API(auth)


def get_url_len():
    auth = OAuth1(twitter_config['consumer_key'],
                  twitter_config['consumer_secret'],
                  twitter_config['access_token'],
                  twitter_config['access_token_secret'])
    return get('https://api.twitter.com/1.1/help/configuration.json', auth=auth).json()['short_url_length']


if __name__ == '__main__':
    members = get_members()
    senators = members[:2]
    senator = senators[0]
    if include_rep:
        rep = members[-1]
    bills = senator.get_bills()
    if bills:
        bill = bills[0]
    votes = senator.get_votes()
    if votes:
        vote = votes[0]
    from pprint import pprint

    import pdb; pdb.set_trace()
