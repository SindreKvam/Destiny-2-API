
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

    def getItemName(self, item_hash):
        return self.manifestInventoryItemDefinition(item_hash).json()['Response']['displayProperties']['name']


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

    def handleItemIndexes(self, indexes, vendor_indexes, vendor_index_list):
        item_owned = False
        item_hash = 0
        for index in range(len(indexes)):
            if str(indexes[index]) in vendor_index_list:
                item_info = vendor_indexes[str(indexes[index])]
                item_hash = item_info['itemHash']
                item_owned = item_info['saleStatus']
                if int(item_owned) == 8 or int(item_owned) == 4096:
                    item_owned = True  # If already owned, change to True
                break
        return item_hash, item_owned

    def getAvailableModsBanshee(self):
        vendor_definition = self.manifestVendorDescription(self.vendorhashes['banshee'])

        weapon_mod_indexes = vendor_definition.json()['Response']['categories'][18]['vendorItemIndexes']    # unsure if the positional argument will work in the future (18)
        armour_mod_indexes = vendor_definition.json()['Response']['categories'][17]['vendorItemIndexes']

        vendor = self.vendors('banshee')

        vendor_item_index = vendor.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        weapon_mod_hash, weapon_mod_owned = self.handleItemIndexes(weapon_mod_indexes, vendor_item_index, vendor_item_index_list)
        armour_mod_hash, armour_mod_owned = self.handleItemIndexes(armour_mod_indexes, vendor_item_index, vendor_item_index_list)

        weapon_mod_name = self.getItemName(weapon_mod_hash)
        armour_mod_name = self.getItemName(armour_mod_hash)

        return {'armour mod': {f'name': f'{armour_mod_name}', f'hash': f'{armour_mod_hash}', 'owned': f'{armour_mod_owned}'},
                'weapon mod': {f'name': f'{weapon_mod_name}', f'hash': f'{weapon_mod_hash}', 'owned': f'{weapon_mod_owned}'}
                }

    def getXurInfo(self):
        vendor_definition = self.manifestVendorDescription(self.vendorhashes['xur'])

        exotic_weapon_indexes = vendor_definition.json()['Response']['categories'][1]['vendorItemIndexes']  # unsure if the positional argument will work in the future (18)
        armour_hunter = vendor_definition.json()['Response']['categories'][2]['vendorItemIndexes']
        armour_titan = vendor_definition.json()['Response']['categories'][3]['vendorItemIndexes']
        armour_warlock = vendor_definition.json()['Response']['categories'][4]['vendorItemIndexes']

        vendor = self.vendors('xur')

        vendor_item_index = vendor.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        exotic_weapon_hash, exotic_weapon_owned = self.handleItemIndexes(exotic_weapon_indexes, vendor_item_index, vendor_item_index_list)

        armour_hunter_hash, armour_hunter_owned = self.handleItemIndexes(armour_hunter, vendor_item_index, vendor_item_index_list)
        armour_titan_hash, armour_titan_owned = self.handleItemIndexes(armour_titan, vendor_item_index, vendor_item_index_list)
        armour_warlock_hash, armour_warlock_owned = self.handleItemIndexes(armour_warlock, vendor_item_index, vendor_item_index_list)

        exotic_weapon_name = self.getItemName(exotic_weapon_hash)
        armour_hunter_name = self.getItemName(armour_hunter_hash)
        armour_titan_name = self.getItemName(armour_titan_hash)
        armour_warlock_name = self.getItemName(armour_warlock_hash)

        return {'Exotic Weapon': {'name': f'{exotic_weapon_name}', 'hash': f'{exotic_weapon_hash}'},
                'Hunter Armour': {'name': f'{armour_hunter_name}', 'hash': f'{armour_hunter_hash}'},
                'Titan Armour': {'name': f'{armour_titan_name}', 'hash': f'{armour_titan_hash}'},
                'Warlock Armour': {'name': f'{armour_warlock_name}', 'hash': f'{armour_warlock_hash}'}
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

    printdict(api.getXurInfo())


    # app.run(debug=True, host='0.0.0.0')
