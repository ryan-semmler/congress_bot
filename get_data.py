import requests
from secrets import geocodio_key, lat, lon, propublica_header
import datetime


location = requests.get(f'https://api.geocod.io/v1/reverse?q={lat},{lon}&fields=cd'
                        f'&api_key={geocodio_key}').json()['results'][2]
state = location['address_components']['state'].lower()
district = location['fields']['congressional_district']['district_number']


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


class Bill:
    def __init__(self, member, data):
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

    def __repr__(self):
        return f"{self.number}: {self.short_title}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return all((self.id == other.id, self.date == other.date))


class Vote:
    def __init__(self, member, data):
        self.member = member
        self.session = data['session']
        self.bill = data['bill']
        self.description = data['description']
        self.question = data['question']
        self.result = data['result']
        year, month, day = [int(thing) for thing in data['date'].split('-')]
        self.date = datetime.date(year, month, day)
        self.position = data['position']
        self.for_passage = 'pass' in self.question.lower()

    def __repr__(self):
        connector = ' '
        if 'to' not in self.description[:2].lower():
            connector += 'on '
        if 'act' in self.description[-3:].lower():
            connector += 'the '
        return f"voted {self.position}{connector}{self.description}."

    def __str__(self):
        return self.__repr__()


# find congresspeople
def get_rep():
    rep_data = requests.get(f"https://api.propublica.org/congress/v1/members/house/{state}/{district}/current.json",
                            headers=propublica_header).json()['results'][0]
    return Member(rep_data)


def get_senators():
    senators_data = requests.get(f"https://api.propublica.org/congress/v1/members/senate/{state}/current.json",
                                 headers=propublica_header).json()['results']
    return [Member(data) for data in senators_data]


# find bills introduced by members
def get_bills(member):
    bill_data = requests.get(f"https://api.propublica.org/congress/v1/members/{member.id}/bills/"
                             "introduced.json", headers=propublica_header).json()['results'][0]['bills']
    return [Bill(member, data) for data in bill_data]


# find votes by members
def get_votes(member):

    # TODO: shorten repr to fit under 140 chars
    vote_data = requests.get(f"https://api.propublica.org/congress/v1/members/{member.id}/votes.json",
                             headers=propublica_header).json()['results'][0]['votes']
    return [Vote(member, data) for data in vote_data]

import pdb; pdb.set_trace()