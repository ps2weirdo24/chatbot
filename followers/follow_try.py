import requests
import json
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()

client_id = "b69qxr73yp8w2qzndu0uf33kfcg4ej7"
head = {"client-id": client_id}
url = "https://api.twitch.tv/kraken/channels/elmagnificotaco/follows?direction=DESC&limit=100"
follow_filename = "follower_data.json"

"""

list_of_follow = []
crit = True
while crit:
	thisone = requests.get(url, headers=head)
	working_dict = thisone.json()
	if working_dict["follows"] == []:
		crit = False
	else:
		for item in working_dict["follows"]:
			this_user = item["user"]["name"]
			list_of_follow.append(this_user)
		url = working_dict["_links"]["next"]

follow_file = open("follower_data.json",'w')
json.dump(list_of_follow, follow_file, indent=4)

print list_of_follow
print len(list_of_follow)

"""

class FollowHandler():
	"""
	A class that handles pulling follower data from the Twitch.tv API
	"""
	def __init__(self, channel):
		self.this_channel = str(channel)
		self.og_url = "https://api.twitch.tv/kraken/channels/%s/follows?direction=DESC&limit=100" % (self.this_channel)
		self.filename = follow_filename
		self.total_follow = self.get_total()
		self.current_list = self.get_list()
		self.check_new()

	def get_total(self):
		total_url = "https://api.twitch.tv/kraken/channels/%s/follows?direction=DESC&limit=1" % (self.this_channel)
		response = requests.get(total_url,headers=head)
		the_total = int(response.json()["_total"])
		return the_total

	def get_list(self):
		temp_open = open(self.filename,"r")
		to_return = list(json.load(temp_open))
		temp_open.close()
		return to_return

	def save_to_file(self):
		temp_open = open(self.filename,"w")
		json.dump(self.current_list, temp_open,indent=4)
		temp_open.close()

	def check_new(self):
		to_return = []
		url = self.og_url
		pulled_follow = []
		crit = True
		while crit:
			thisone = requests.get(url, headers=head)
			working_dict = thisone.json()
			if working_dict["follows"] == []:
				crit = False
			else:
				for item in working_dict["follows"]:
					this_user = item["user"]["name"]
					pulled_follow.append(this_user)
					url = working_dict["_links"]["next"]
		for item in pulled_follow:
			if item not in self.current_list:
				to_return.append(item)
				self.current_list.append(item)
			else:
				pass
		self.save_to_file()
		return to_return

if __name__ == "__main__":
	this_debug = FollowHandler("elmagnificotaco")
