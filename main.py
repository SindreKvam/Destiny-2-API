
import requests
#http://destinydevs.github.io/BungieNetPlatform/docs/Getting-Started
#https://www.bungie.net/en/Application/Detail/38058
#https://bungie-net.github.io/multi/index.html

HEADERS ={"X-API-Key":"e215911472b5409f8c0257b6054b6371"}
USER_ID = "18736344"
DESTINY_ID = "76561198095815307"
ENDPOINT = "https://www.bungie.net/Platform"

bungieUser = requests.get(ENDPOINT+f"/User/GetBungieNetUserById/{USER_ID}/", headers=HEADERS)
print(bungieUser.json()['Response']['displayName'])

#Get User info (Only mine)
destinyUser = requests.get(ENDPOINT+f"/User/GetBungieAccount/{USER_ID}/254/",headers=HEADERS)
destinyUserArray = destinyUser.json()['Response']['destinyMemberships'][0]
membershipId = destinyUserArray['membershipId']
membershipType = destinyUserArray['membershipType']

#Clan Reward Status
clanReward = requests.get(ENDPOINT+f"/Destiny2/Clan/{2802086}/WeeklyRewardState/",headers=HEADERS)
for i in range(4):
    print(clanReward.json()['Response']['rewards'][0]['entries'][i])
