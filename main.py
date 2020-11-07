
import requests
from requests_oauthlib import OAuth2Session
from definitions import printjson
import json

# http://destinydevs.github.io/BungieNetPlatform/docs/Getting-Started
# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html

with open('config.json') as config_file:
    config = json.load(config_file)


API_KEY = config['APIkey']
HEADERS = {"X-API-Key":f"{API_KEY}"}
USER_ID = config["UserId"]
CLIENT_ID = config["ClientId"]
CLAN_ID = config['ClanId']

ENDPOINT = "https://www.bungie.net/Platform"


# bungieUser = requests.get(ENDPOINT+f"/User/GetBungieNetUserById/{USER_ID}/", headers=HEADERS)
# print(bungieUser.json()['Response'])
"""
# Get User info (Only mine)
destinyUser = requests.get(f"{ENDPOINT}/User/GetBungieAccount/{USER_ID}/254/", headers=HEADERS)
destinyUserArray = destinyUser.json()['Response']['destinyMemberships'][0]
membershipId = destinyUserArray['membershipId']
membershipType = destinyUserArray['membershipType']
"""


redirect_uri = 'https://destinygetauth-key.no/'

oauth = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri)
authorization_url, state = oauth.authorization_url(
        'https://www.bungie.net/en/oauth/authorize',
        # parameters.
        # access_type="offline", prompt="select_account"
        state="6i0mkLx79Hp91nzWVeHrzHG4"    # Random code here just to see what the API responds to.
        )


print(f'Please go to {authorization_url} and authorize access.')
authorization_response = input('Enter the full callback URL ')

token = oauth.fetch_token(
        'https://www.bungie.net/platform/app/oauth/token',
        authorization_response=authorization_response,
        include_client_id=True,
        # authentication
        )
access_token = token['access_token']

signedIn = oauth.get(
    f'{ENDPOINT}/User/GetMembershipsForCurrentUser/',
    headers=HEADERS
)
print("Signed in information")
printjson(signedIn)


print("Clan Reward Status")
clanReward = requests.get(f"{ENDPOINT}/Destiny2/Clan/{CLAN_ID}/WeeklyRewardState/", headers=HEADERS)
printjson(clanReward)
for i in range(4):
    print(clanReward.json()['Response']['rewards'][0]['entries'][i])

# Pull from Postmaster
pullPostmaster = requests.post(
    f"{ENDPOINT}/Destiny2/Actions/Items/PullFromPostmaster/",
    headers=HEADERS,
    )
printjson(pullPostmaster)


