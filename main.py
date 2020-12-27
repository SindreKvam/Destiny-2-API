
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
header = {'X-API-Key': f'{API_KEY}'}
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

        self.info()

#    @app.route('/login')
#    def login(self):
#        print(f'Please go to {authorization_url} and authorize access.')
#
#        return render_template('login.html')

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
            headers=header
        )

        response_destiny = signed_in.json()['Response']['destinyMemberships'][0]
        response_bungie = signed_in.json()['Response']['bungieNetUser']

        self.membership_type = response_destiny['membershipType']   # membership type: 3 (steam)
        self.membership_id = response_destiny['membershipId']       # steam membership ID
        self.membership_id_bungie = response_bungie['membershipId']

        signed_in = oauth.get(
            f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/?components=100',
            headers=header
        )

        # Character Id's
        self.character_id = signed_in.json()['Response']['profile']['data']['characterIds']
        self.character1 = self.character_id[0]
        self.character2 = self.character_id[1]
        self.character3 = self.character_id[2]

    def locales(self):
        locales = oauth.get(
            f'{endpoint}/GetAvailableLocales/',
            headers=header
        )
        return locales

    def vendors(self, vendor):
        vendorhashes = {
            'all': '',
            'xur': '2190858386/',
            'banshee': '672118013/',
            'tess-everis': '3361454721/',
            'zavala': '69482069/',

        }
        if vendor in vendorhashes.keys():
            vendors = oauth.get(
                f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/Character/{self.character2}'
                f'/Vendors/{vendorhashes[vendor]}?description=True&components=402',
                headers=header
            )
            return vendors
        else:
            raise ValueError(f'Not a valid vendor, valid vendors are: {list(vendorhashes.keys())}')

    def availableModsBanshee(self):
        vendors = self.vendors('banshee')

        vendor_item_index = vendors.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        mods = {
            '179977568': 'grasp of the warmind',
            '2597888510': 'cellular supression',
            '2597888511': 'power of rasputin',
            '2597888509': 'warminds longevity',
            '2597888508': 'warminds protection',
            '179977575': 'warminds light',
            '179977573': 'blessing of rasputin',
            '2216063963': 'burning cells',
            '2216063961': 'fireteam medic',
            '1789319806': 'modular lightning'
        }

        sale_status = []
        banshee_sales = []
        for i in vendor_item_index_list:
            sale_status.append(vendor_item_index[i]['saleStatus'])
            banshee_sales.append(vendor_item_index[i]['itemHash'])

        for i in range(len(banshee_sales)):
            if str(banshee_sales[i]) in list(mods.keys()):
                return mods[str(banshee_sales[i])]

        return None
#        if f'{mod_id}' in list(mods.keys()):
#            return mods[f'{mod_id}']
#        else:
#            return mod_id

    def getItemInfo(self, itemID):
        item = oauth.get(
            f'{endpoint}/Content/GetContentById/{itemID}/en/',
            headers=header
        )
        return item

    def clanstatus(self):
        print("Clan Reward Status")
        clanReward = requests.get(
            f"{endpoint}/Destiny2/Clan/{CLAN_ID}/WeeklyRewardState/",
            headers=header
        )
        printjson(clanReward)
        for i in range(4):
            print(clanReward.json()['Response']['rewards'][0]['entries'][i])

    def pullfrompostmaster(self):
        print("Pull from Postmaster")
        pullPostmaster = oauth.post(
            f"{endpoint}/Destiny2/Actions/Items/PullFromPostmaster/",
            headers=header,
            data={'characterId': f'{self.character3}',
                  'membershipType': f'{self.membership_type}'}
            )
        printjson(pullPostmaster)


if __name__ == '__main__':
    api = Api()
    #printjson(api.getItemInfo(api.availableModsBanshee()))
    #printjson(api.vendors('banshee'))
    #api.pullfrompostmaster()
    print(api.availableModsBanshee())
    # app.run(debug=True, host='0.0.0.0')


# Destiny.Entities.Vendors.DestinyVendorCategory
# /Destiny2/{membershipType}/Profile/{destinyMembershipId}/Character/{characterId}/Vendors/