
import requests

#https://www.bungie.net/en/Application/Detail/38058

HEADERS ={"X-API-Key":"e215911472b5409f8c0257b6054b6371"}
USER_ID = "18736344"
ENDPOINT = "https://www.bungie.net/Platform"

r = requests.get(ENDPOINT+f"/User/GetBungieNetUserById/{USER_ID}/ ", headers=HEADERS)


item = r.json()
print(item['profilePicture'])