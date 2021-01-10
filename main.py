
import requests
import json
import numpy as np
from time import sleep, time
from tqdm import tqdm
from requests_oauthlib import OAuth2Session
from definitions import printjson, printdict
from flask import Flask, render_template, request, redirect

# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html
# components = https://bungie-net.github.io/multi/schema_Destiny-DestinyComponentType.html

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
    character_ids = None

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
        self.character_ids = signed_in.json()['Response']['profile']['data']['characterIds']

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

    def get_vendors(self, vendor='all'):
        if vendor in self.vendorhashes.keys():
            vendors = oauth.get(
                f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}/Character/{self.character_ids[0]}'
                f'/Vendors/{self.vendorhashes[vendor]}?description=True&components=402',
                headers=header
            )
            return vendors
        else:
            raise ValueError(f'Not a valid vendor, valid vendors are: {list(self.vendorhashes.keys())}')

    def get_character(self, character_num):
        primary_slot = []
        secondary_slot = []
        heavy_slot = []
        equipped_items = []

        character_info = oauth.get(
            f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}'
            f'/Character/{self.character_ids[character_num-1]}'
            f'/?components=Characters,CharacterInventories,CharacterEquipment',
            headers=header
        )
        item_list = character_info.json()['Response']['inventory']['data']['items']

        for i in range(len(item_list)):
            item_hash = item_list[i]['itemHash']

            if item_list[i]['bucketHash'] == 1498876634:
                item_name = self.getItemName(item_hash)
                primary_slot.append({
                    'itemName': f'{item_name}',
                    'itemHash': f'{item_hash}',
                    'itemInstanceId': f'{item_list[i]["itemInstanceId"]}'})
            elif item_list[i]['bucketHash'] == 2465295065:
                item_name = self.getItemName(item_hash)
                secondary_slot.append({
                    'itemName': f'{item_name}',
                    'itemHash': f'{item_hash}',
                    'itemInstanceId': f'{item_list[i]["itemInstanceId"]}'})
            elif item_list[i]['bucketHash'] == 953998645:
                item_name = self.getItemName(item_hash)
                heavy_slot.append({
                    'itemName': f'{item_name}',
                    'itemHash': f'{item_hash}',
                    'itemInstanceId': f'{item_list[i]["itemInstanceId"]}'})

        equipped_item_list = character_info.json()['Response']['equipment']['data']['items']
        for i in range(8):
            item_hash = equipped_item_list[i]['itemHash']
            item_name = self.getItemName(item_hash)
            equipped_items.append({
                'itemName': f'{item_name}',
                'itemHash': f'{item_hash}',
                'itemInstanceId': f'{equipped_item_list[i]["itemInstanceId"]}'})

        return {'primary weapons': f'{primary_slot}',
                'secondary weapons': f'{secondary_slot}',
                'heavy weapons': f'{heavy_slot}',
                'equipped weapons': f'{equipped_items}'}

    def get_detailed_item_info(self, item_instance_id):
        item_info = oauth.get(
            f'{endpoint}/Destiny2/{self.membership_type}/Profile/{self.membership_id}'
            f'/Item/{item_instance_id}/?components=ItemInstances,ItemPerks,ItemStats,ItemCommonData',
            headers=header
        )
        return item_info.json()

    def get_vendor_info(self):
        vendor_names = []
        vendor_subtitles = []
        vendor_identifier = []
        vendor_description = []

        vendor_info = {}

        vendor_hashes = list(self.get_vendors().json()['Response']['sales']['data'].keys())
        print('fetching vendor information: ')
        for i in tqdm(range(len(vendor_hashes))):
            vendor_manifest = self.manifestVendorDescription(vendor_hashes[i]).json()

            vendor_names.append(vendor_manifest['Response']['displayProperties']['name'])
            vendor_subtitles.append(vendor_manifest['Response']['displayProperties']['subtitle'])
            vendor_identifier.append(vendor_manifest['Response']['vendorIdentifier'])
            vendor_description.append(vendor_manifest['Response']['displayProperties']['description'])

            vendor_info[vendor_names[i]] = {'hash': f'{vendor_hashes[i]}',
                                                 'subtitle': f'{vendor_subtitles[i]}',
                                                 'identifier': f'{vendor_identifier[i]}',
                                                 'description': f'{vendor_description[i]}'}
        return vendor_info

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
        vendor_definition = self.manifestVendorDescription('672118013')

        # unsure if the positional argument will work in the future (18)
        weapon_mod_indexes = vendor_definition.json()['Response']['categories'][18]['vendorItemIndexes']
        armor_mod_indexes = vendor_definition.json()['Response']['categories'][17]['vendorItemIndexes']

        vendor = self.get_vendors('banshee')

        vendor_item_index = vendor.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        weapon_mod_hash, weapon_mod_owned = self.handleItemIndexes(
                                            weapon_mod_indexes, vendor_item_index, vendor_item_index_list)
        armor_mod_hash, armor_mod_owned = self.handleItemIndexes(
                                            armor_mod_indexes, vendor_item_index, vendor_item_index_list)

        weapon_mod_name = self.getItemName(weapon_mod_hash)
        armor_mod_name = self.getItemName(armor_mod_hash)

        return {'armor mod': {f'name': f'{armor_mod_name}', 
                               f'hash': f'{armor_mod_hash}', 
                               'owned': f'{armor_mod_owned}'},
                'weapon mod': {f'name': f'{weapon_mod_name}', 
                               f'hash': f'{weapon_mod_hash}', 
                               'owned': f'{weapon_mod_owned}'}
                }

    def getXurInventory(self):
        vendor_definition = self.manifestVendorDescription('2190858386')

        exotic_weapon_indexes = vendor_definition.json()['Response']['categories'][1]['vendorItemIndexes']
        armor_hunter = vendor_definition.json()['Response']['categories'][2]['vendorItemIndexes']
        armor_titan = vendor_definition.json()['Response']['categories'][3]['vendorItemIndexes']
        armor_warlock = vendor_definition.json()['Response']['categories'][4]['vendorItemIndexes']

        vendor = self.get_vendors('xur')

        if vendor.json()['ErrorCode'] == 1627:
            return vendor.json()['Message']

        vendor_item_index = vendor.json()['Response']['sales']['data']
        vendor_item_index_list = list(vendor_item_index.keys())

        exotic_weapon_hash, exotic_weapon_owned = self.handleItemIndexes(
                                                exotic_weapon_indexes, vendor_item_index, vendor_item_index_list)
        armor_hunter_hash, armor_hunter_owned = self.handleItemIndexes(
                                                armor_hunter, vendor_item_index, vendor_item_index_list)
        armor_titan_hash, armor_titan_owned = self.handleItemIndexes(
                                                armor_titan, vendor_item_index, vendor_item_index_list)
        armor_warlock_hash, armor_warlock_owned = self.handleItemIndexes(
                                                armor_warlock, vendor_item_index, vendor_item_index_list)

        exotic_weapon_name = self.getItemName(exotic_weapon_hash)
        armor_hunter_name = self.getItemName(armor_hunter_hash)
        armor_titan_name = self.getItemName(armor_titan_hash)
        armor_warlock_name = self.getItemName(armor_warlock_hash)

        return {'Exotic Weapon': {'name': f'{exotic_weapon_name}', 'hash': f'{exotic_weapon_hash}'},
                'Hunter': {'name': f'{armor_hunter_name}', 'hash': f'{armor_hunter_hash}'},
                'Titan': {'name': f'{armor_titan_name}', 'hash': f'{armor_titan_hash}'},
                'Warlock': {'name': f'{armor_warlock_name}', 'hash': f'{armor_warlock_hash}'}
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

    def pullfrompostmaster(self, character, item_id, item_reference_hash):
        print("Pull from Postmaster")
        if 0 > character > 2:
            raise ValueError('choose a character between 1-3')
        pull_postmaster_response = oauth.post(
            f"{endpoint}/Destiny2/Actions/Items/PullFromPostmaster/",
            headers=header,
            data={'characterId': f'{self.character_ids[character-1]}',
                  'membershipType': f'{self.membership_type}',
                  'itemId': f'{item_id}',
                  'itemReferenceHash': f'{item_reference_hash}'}
            )
        printjson(pull_postmaster_response)

    def raidReportCardLink(self):
        print(f'https://raid.report/pc/{self.membership_id}')



if __name__ == '__main__':
    api = BungieApi()
    # printdict(api.getManifest())
    printdict(api.get_character(3))
    # printdict(api.get_detailed_item_info(6917529201513267083))
    # printdict(api.getAvailableModsBanshee())
    # printdict(api.getXurInventory())

    # printdict(api.get_vendor_info())

    # app.run(debug=True, host='0.0.0.0')
