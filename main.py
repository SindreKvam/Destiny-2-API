
import requests
import json
from requests_oauthlib import OAuth2Session
from definitions import printjson, printdict
from flask import Flask, render_template, request, redirect

# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html

# Extracting what's in the config file and putting it in a dictionary called config
with open('config.json') as config_file:
    config = json.load(config_file)

# start the Flask application
app = Flask(__name__)

# Collecting inputs from the config file
api_key = config['APIkey']
client_id = config['ClientId']
clan_id = config['ClanId']

# Set the header for when sending requests
header = {'X-API-Key': f'{api_key}'}

# Set the endpoint that's going to be used for the requests sent
endpoint = "https://www.bungie.net/Platform"

# redirect uri, must match the application on https://www.bungie.net/developer
redirect_uri = 'https://destinygetauth-key.no/'

# Setting up oauth
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
authorization_url, state = oauth.authorization_url(
        'https://www.bungie.net/en/oauth/authorize'
        # state='random numbers', isn't needed but can be used to always recognize which process is responded to
        )


class BungieApi:
    unique_name = None
    membership_type = None
    membership_id = None
    membership_id_bungie = None
    character_id = None
    character1 = None
    character2 = None
    character3 = None

    vendorhashes = {
        'all': '',
        'xur': '2190858386/',
        'banshee': '672118013/',
        'tess-everis': '3361454721/',
        'zavala': '69482069/',

    }

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

    def getManifest(self):
        manifest = oauth.get(
            f'{endpoint}/Destiny2/Manifest/',
            headers=header
        )
        manifest_en = manifest.json()['Response']['jsonWorldComponentContentPaths']['en']
        return manifest_en

    def manifestVendorDescription(self, vendor_hash):
        vendor_definition = oauth.get(
            f'{endpoint}/Destiny2/Manifest/DestinyVendorDefinition/{vendor_hash}',
            headers=header
        )

        return vendor_definition

    def manifestInventoryItemDefinition(self, item_hash):
        inventory_item_definition = oauth.get(
            f'{endpoint}/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}',
            headers=header
        )
        return inventory_item_definition

    def locales(self):
        locales = oauth.get(
            f'{endpoint}/GetAvailableLocales/',
            headers=header
        )
        return locales

    def vendors(self, vendor):
        if vendor in self.vendorhashes.keys():
            vendors = oauth.get(
                f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/Character/{self.character2}'
                f'/Vendors/{self.vendorhashes[vendor]}?description=True&components=402',
                headers=header
            )
            return vendors
        else:
            raise ValueError(f'Not a valid vendor, valid vendors are: {list(self.vendorhashes.keys())}')

    def getAvailableModsBanshee(self):
        vendor_definition = self.manifestVendorDescription(self.vendorhashes['banshee'])

        weapon_mod_indexes = vendor_definition.json()['Response']['categories'][18]['vendorItemIndexes']
        armour_mod_indexes = vendor_definition.json()['Response']['categories'][17]['vendorItemIndexes']

        vendor = self.vendors('banshee')

        vendor_item_index = vendor.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        weapon_mod_owned = False
        weapon_mod_hash = 0
        for index in range(len(weapon_mod_indexes)):
            if str(weapon_mod_indexes[index]) in vendor_item_index_list:
                weapon_mod_info = vendor_item_index[str(weapon_mod_indexes[index])]
                weapon_mod_hash = weapon_mod_info['itemHash']
                weapon_mod_owned = weapon_mod_info['saleStatus']
                if int(weapon_mod_owned) != 0:
                    weapon_mod_owned = True      # If already owned, change to True
                break

        armour_mod_owned = False
        armour_mod_hash = 0
        for index in range(len(armour_mod_indexes)):
            if str(armour_mod_indexes[index]) in vendor_item_index_list:
                armour_mod_info = vendor_item_index[str(armour_mod_indexes[index])]
                armour_mod_hash = armour_mod_info['itemHash']
                armour_mod_owned = armour_mod_info['saleStatus']
                if int(armour_mod_owned) == 8 or int(armour_mod_owned) == 4096:
                    armour_mod_owned = True      # If already owned, change to True
                break

        weapon_mod_name = self.manifestInventoryItemDefinition(weapon_mod_hash).json()['Response']['displayProperties']['name']
        armour_mod_name = self.manifestInventoryItemDefinition(armour_mod_hash).json()['Response']['displayProperties']['name']
        printdict(self.manifestInventoryItemDefinition(armour_mod_hash).json())
        return {'armour mod': {f'name': f'{armour_mod_name}', f'hash': f'{armour_mod_hash}', 'owned': f'{armour_mod_owned}'},
                'weapon mod': {f'name': f'{weapon_mod_name}', f'hash': f'{weapon_mod_hash}', 'owned': f'{weapon_mod_owned}'}
                }

    def clanstatus(self):
        print("Clan Reward Status")
        clanReward = requests.get(
            f"{endpoint}/Destiny2/Clan/{clan_id}/WeeklyRewardState/",
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
    api = BungieApi()
    #printdict(api.getManifest())
    printdict(api.getAvailableModsBanshee())

    # app.run(debug=True, host='0.0.0.0')
