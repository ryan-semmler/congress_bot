import requests
from secrets import Secrets

secrets = Secrets()

location = requests.get(f'https://api.geocod.io/v1/reverse?q={secrets.lat},{secrets.lon}&fields=cd'
                        f'&api_key={secrets.geocodio_key}').json()['results'][2]

state = location['address_components']['state'].lower()
district = location['fields']['congressional_district']['district_number']

senators_data = requests.get(f"https://api.propublica.org/congress/v1/members/senate/{state}/current.json",
                             headers=secrets.propublica_header).json()['results']
rep_data = requests.get(f"https://api.propublica.org/congress/v1/members/house/{state}/{district}/current.json")


class Member:
    def __init__(self, data):
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
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


senators = [Member(data) for data in senators_data]
rep = Member(rep_data)

# find congresspeople
def get_rep(location):
    pass
def get_senators(state):
    pass


# find bills introduced by members
def sen_get_bills():
    pass
def house_get_bills():
    pass


# find votes by members
def sen_get_votes():
    pass
def house_get_votes():
    pass
