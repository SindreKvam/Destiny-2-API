
import requests
from requests_oauthlib import OAuth2Session
from definitions import printjson
from flask import Flask, render_template, request, redirect
import json

# http://destinydevs.github.io/BungieNetPlatform/docs/Getting-Started
# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html

with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)

# Collecting inputs from the config file
API_KEY = config['APIkey']
HEADERS = {"X-API-Key": f"{API_KEY}"}
CLIENT_ID = config["ClientId"]
CLAN_ID = config['ClanId']

# Start link for almost all requests
ENDPOINT = "https://www.bungie.net/Platform"

redirect_uri = 'https://destinygetauth-key.no/'

oauth = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri)
authorization_url, state = oauth.authorization_url(
        'https://www.bungie.net/en/oauth/authorize'
        # state='random numbers', isn't needed but can be used to always recognize which process is responded to
        )


# print(f'Please go to {authorization_url} and authorize access.')
# authorization_response = input('Enter the full callback URL ')

# token = oauth.fetch_token(
#        'https://www.bungie.net/platform/app/oauth/token',
#        authorization_response=authorization_response,
#        include_client_id=True,
#        # authentication
#        )
# access_token = token['access_token']

@app.route('/login')
def login():
    print(f'Please go to {authorization_url} and authorize access.')

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    authorization_response = request.form['login']
    token = oauth.fetch_token(
        'https://www.bungie.net/platform/app/oauth/token',
        authorization_response=authorization_response,
        include_client_id=True,
        # authentication
    )
    access_token = token['access_token']
    return redirect('/info')


@app.route('/')
def index():
    return 'Hello world'


@app.route('/info')
def info():
    print("Signed in information")
    signedIn = oauth.get(   # oauth.get instead of request.get because auth code is saved in oauth library.
        f'{ENDPOINT}/User/GetMembershipsForCurrentUser/',
        headers=HEADERS
    )
    printjson(signedIn)

    MEMBERSHIP_TYPE = signedIn.json()['Response']['destinyMemberships'][0]['membershipType']
    USER_ID = signedIn.json()['Response']['bungieNetUser']['membershipId']
    return redirect('/')


def clanstatus():
    print("Clan Reward Status")
    clanReward = requests.get(
        f"{ENDPOINT}/Destiny2/Clan/{CLAN_ID}/WeeklyRewardState/",
        headers=HEADERS
    )
    printjson(clanReward)
    for i in range(4):
        print(clanReward.json()['Response']['rewards'][0]['entries'][i])


def pullfrompostmaster():
    print("Pull from Postmaster")
    pullPostmaster = oauth.post(
        f"{ENDPOINT}/Destiny2/Actions/Items/PullFromPostmaster/",
        headers=HEADERS,
        )
    printjson(pullPostmaster)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
