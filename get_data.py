import requests
from config import state, district, propublica_header
import datetime


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
        if type(other) != Bill:
            return False
        return all((self.id == other.id, self.date == other.date))


class Vote:
    def __init__(self, member, data):
        self.member = member
        self.session = data['session']
        try:
            self.bill = get_bill_by_id(member, data['bill']['bill_id'])
        except:
            self.bill = data['bill']
        self.description = data['description']
        self.question = data['question']
        self.result = data['result']
        year, month, day = [int(thing) for thing in data['date'].split('-')]
        self.date = datetime.date(year, month, day)
        self.position = data['position'].lower()
        self.for_passage = 'pass' in self.question.lower()

    def __repr__(self):
        connector = ' '
        if 'to' not in self.description[:2].lower():
            connector += 'on '
        if 'Act' in self.description:
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


def get_bill_by_id(member, id):
    bill_id, congress = id.split('-')
    bill_data = requests.get(f"https://api.propublica.org/congress/v1/{congress}/bills/{bill_id}.json",
                             headers=propublica_header).json()['results'][0]
    return Bill(member, bill_data)


# find congresspeople
def get_rep():
    rep_data = requests.get(f"https://api.propublica.org/congress/v1/members/house/{state}/{district}/current.json",
                            headers=propublica_header).json()['results'][0]
    return [Member(rep_data)]


def get_senators():
    senators_data = requests.get(f"https://api.propublica.org/congress/v1/members/senate/{state}/current.json",
                                 headers=propublica_header).json()['results']
    return [Member(data) for data in senators_data]


# find bills introduced by members
def get_bills(member):
    bill_data = requests.get(f"https://api.propublica.org/congress/v1/members/{member.id}/bills/"
                             "introduced.json", headers=propublica_header).json()['results'][0]['bills']
    return [Bill(member, data) for data in bill_data]


def include_vote(vote):
    return any([word in vote.question.lower() for word in ("pass", "agree", "nomination", "resolution")])


# find votes by members
def get_votes(member):
    vote_data = requests.get(f"https://api.propublica.org/congress/v1/members/{member.id}/votes.json",
                             headers=propublica_header).json()['results'][0]['votes']
    all_votes = [Vote(member, data) for data in vote_data]
    return [vote for vote in all_votes if include_vote(vote)][::-1]


if __name__ == '__main__':
    senators = get_senators()
    thom = senators[0]
    bills = get_bills(thom)
    bill = get_bills(thom)[0]
    votes = get_votes(thom)
    vote = get_votes(thom)[0]
    from app import days_old

    new_vote_data = {'member_id': 'T000476', 'chamber': 'Senate', 'congress': '115', 'session': '1', 'roll_call': '280',
                     'vote_uri': 'https://api.propublica.org/congress/v1/115/senate/sessions/1/votes/280.json',
                     'bill': {'bill_id': 's2126-115', 'number': 'PN875', 'api_uri': None, 'title': None,
                              'latest_action': None}, 'amendment': {},
                     'nomination': {'nomination_id': 'PN875-115', 'number': 'PN875', 'name': 'Donald C. Coggins Jr.',
                                    'agency': 'The Judiciary'},
                     'description': 'Donald C. Coggins, Jr., of South Carolina, to be United States District Judge for the District of South Carolina',
                     'question': 'On the Nomination', 'result': 'Nomination Confirmed', 'date': '2017-11-16',
                     'time': '13:48:00', 'total': {'yes': 96, 'no': 0, 'present': 0, 'not_voting': 4},
                     'position': 'Yes'}
    new_vote = Vote(thom, new_vote_data)
    import pdb;pdb.set_trace()
