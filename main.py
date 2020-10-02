
import requests

# http://destinydevs.github.io/BungieNetPlatform/docs/Getting-Started
# https://www.bungie.net/en/Application/Detail/38058
# https://bungie-net.github.io/multi/index.html
# http://allynh.com/blog/creating-a-python-app-for-destiny-part-3-logging-in-to-bungie-net-and-authenticating-with-psn/

API_KEY = "e215911472b5409f8c0257b6054b6371"
HEADERS ={"X-API-Key":f"{API_KEY}"}
USER_ID = "18736344"
CLIENT_ID = "33666"
ENDPOINT = "https://www.bungie.net/Platform"
YAWRON_CLAN_ID = "2802086"

bungieUser = requests.get(ENDPOINT+f"/User/GetBungieNetUserById/{USER_ID}/", headers=HEADERS)
print(bungieUser.json()['Response'])

# Get User info (Only mine)
destinyUser = requests.get(ENDPOINT+f"/User/GetBungieAccount/{USER_ID}/254/", headers=HEADERS)
destinyUserArray = destinyUser.json()['Response']['destinyMemberships'][0]
membershipId = destinyUserArray['membershipId']
membershipType = destinyUserArray['membershipType']

# sign in
Authentication = requests.get(f"https://www.bungie.net/en/oauth/authorize?client_id={CLIENT_ID}&response_type=code")  #&state=6i0mkLx79Hp91nzWVeHrzHG4
# get the bungled and bungleatk cookie https://www.bungie.net/en/Groups/Post?groupId=39966&postId=85087279&sort=0&page=0&path=1&showBanned=0
# cookies =
print(Authentication)
r = requests.post(f"https://www.bungie.net/platform/app/oauth/token/", data=f"{CLIENT_ID}&grant_type=authorization_code&code={Authentication}")
print(r)

print(requests.get("https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/").json())


# Clan Reward Status
#clanReward = requests.get(ENDPOINT+f"/Destiny2/Clan/{YAWRON_CLAN_ID}/WeeklyRewardState/", headers=HEADERS)
#for i in range(4):
#    print(clanReward.json()['Response']['rewards'][0]['entries'][i])




#pullPostmaster = requests.post(ENDPOINT+f"/Destiny2/Actions/Items/PullFromPostmaster/", headers=HEADERS)
#print(pullPostmaster.json())
