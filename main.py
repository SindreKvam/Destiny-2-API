
import requests
from requests_oauthlib import OAuth2Session
from definitions import printjson
from flask import Flask, render_template, request, redirect
import json

# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html

with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)

# Collecting inputs from the config file
API_KEY = config['APIkey']
HEADERS = {'X-API-Key': f'{API_KEY}'}
CLIENT_ID = config['ClientId']
CLAN_ID = config['ClanId']

# Start link for almost all requests
endpoint = "https://www.bungie.net/Platform"

# redirect uri, must match the application on https://www.bungie.net/developer
redirect_uri = 'https://destinygetauth-key.no/'

oauth = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri)
authorization_url, state = oauth.authorization_url(
        'https://www.bungie.net/en/oauth/authorize'
        # state='random numbers', isn't needed but can be used to always recognize which process is responded to
        )


class Api:
    unique_name = None
    membership_type = None
    membership_id = None
    membership_id_bungie = None
    character_id = None

    def __init__(self):
        print(f'Please go to {authorization_url} and authorize access.')
        authorization_response = input('Enter the full callback URL: ')
        # authorization_response = request.form['login']
        token = oauth.fetch_token(
            'https://www.bungie.net/platform/app/oauth/token',
            authorization_response=authorization_response,
            include_client_id=True,
            # authentication
        )
        access_token = token['access_token']

#    @app.route('/login')
#    def login(self):
#        print(f'Please go to {authorization_url} and authorize access.')
#
#        return render_template('login.html')


#    @app.route('/login', methods=['POST'])
#    def login_post(self):
#        authorization_response = request.form['login']
#        token = oauth.fetch_token(
#            'https://www.bungie.net/platform/app/oauth/token',
#            authorization_response=authorization_response,
#            include_client_id=True,
            # authentication
#        )
#        access_token = token['access_token']
#        return redirect('/info')

#    @app.route('/')
#    def index(self):
#        return render_template('index.html')

#    @app.route('/', methods=['POST'])
#    def index_post(self):
#        if request.form['login']:
#            return redirect('/login')
#        if request.form['info']:
#            return redirect('/info')

#    @app.route('/info')
    def info(self):
        signed_in = oauth.get(   # oauth.get instead of request.get because auth code is saved in oauth library.
            f'{endpoint}/User/GetMembershipsForCurrentUser/',
            headers=HEADERS
        )
        printjson(signed_in)

        response_destiny = signed_in.json()['Response']['destinyMemberships'][0]
        response_bungie = signed_in.json()['Response']['bungieNetUser']

        self.membership_type = response_destiny['membershipType']
        self.membership_id = response_destiny['membershipId']
        self.membership_id_bungie = response_bungie['membershipId']
        self.unique_name = response_bungie['uniqueName']

        signed_in_2 = oauth.get(
            f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/',
            headers=HEADERS
        )
        printjson(signed_in_2)

    def vendors(self):
        vendors = oauth.get(
            f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/Character/{self.character_id}/Vendors/', # characterId
            headers=HEADERS
        )
        return vendors

    def clanstatus(self):
        print("Clan Reward Status")
        clanReward = requests.get(
            f"{endpoint}/Destiny2/Clan/{CLAN_ID}/WeeklyRewardState/",
            headers=HEADERS
        )
        printjson(clanReward)
        for i in range(4):
            print(clanReward.json()['Response']['rewards'][0]['entries'][i])

    def pullfrompostmaster(self):
        print("Pull from Postmaster")
        pullPostmaster = oauth.post(
            f"{endpoint}/Destiny2/Actions/Items/PullFromPostmaster/",
            headers=HEADERS,
            )
        printjson(pullPostmaster)


if __name__ == '__main__':
    api = Api()
    api.info()
    #printjson(api.vendors())
    # app.run(debug=True, host='0.0.0.0')


# Destiny.Entities.Vendors.DestinyVendorCategory
# /Destiny2/{membershipType}/Profile/{destinyMembershipId}/Character/{characterId}/Vendors/