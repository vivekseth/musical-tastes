import secrets

import pygn
import base64
import pickle
import random
import requests
import collections
import multiprocessing


pgyn_clientID = secrets.pgyn_clientID
pgyn_userID = secrets.pgyn_userID

# Utility

def load_pickled_data(pickle_file, gen_func):
	data = None

	try:
		data = pickle.load(open(pickle_file, "rb"))
	except IOError:
		# if no pickle data exists
		data = gen_func()
		pickle.dump(data, open(pickle_file, "wb"))

	return data

def refresh_access(_client_id, _client_secret, access_data):
	
	def replace_access_fields(new_access_data):
		fields = ['access_token', 'token_type', 'expires_in']
		for f in fields:
			access_data[f] = new_access_data[f]
	
	url = 'https://accounts.spotify.com/api/token'
	headers = {
		'Authorization': 'Basic ' + base64.b64encode(_client_id + ':' + _client_secret)
	}
	body = {
		'grant_type': 'refresh_token',
		'refresh_token': access_data['refresh_token']
	}

	r = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=body)
	new_access_data = r.json()
	new_access_data['refresh_token'] = access_data['refresh_token']

	replace_access_fields(new_access_data)
	pickle.dump(new_access_data, open('access_data.p', "wb"))

	return new_access_data

def api_call(access_data, endpoint):
	headers = {
		'Authorization': 'Bearer ' + access_data['access_token']
	}
	base_url = 'https://api.spotify.com/v1'
	endpoint = endpoint

	r = requests.get(base_url + endpoint, headers=headers)
	return r.json()

def safe_api_call(access_data, endpoint):
	data = api_call(access_data, endpoint)
	if 'error' in data and data['error']['status'] == 401:
		# print 'need to refresh...',
		new_access_data = refresh_access(_client_id, _client_secret, access_data)
		# print 'done'
		new_data = api_call(new_access_data, endpoint)
		return new_data
	else:
		return data

# Application Functions

# def load_oauth_access_data():
# 	def gen_fun():
# 		o = SpotifyOAuth(_client_id, _client_secret, _redirect_uri, _scope_string)
# 		access_data = o.get_access_code()
# 		return access_data

# 	return load_pickled_data('access_data.p', gen_fun)

def load_track_list(access_data):
	return load_pickled_data('all_tracks.p', lambda : get_all_tracks(access_data))

def get_all_tracks(access_data):
	all_tracks = []

	should_cont = True
	next_url = '/me/tracks?offset=0&limit=50'
	while(should_cont):
		print next_url,
		data = safe_api_call(access_data, next_url)
		print 'done'

		if 'next' not in data:
			# print data
			continue

		tracks = data['items']
		for t in tracks:
			t_data = {
				'title': t['track']['name'],
				'album': t['track']['album']['name']
			}
			all_tracks.append(t_data)
		
		full_next_url = data['next']
		if full_next_url:
			next_url = full_next_url.replace('https://api.spotify.com/v1', '')
		else:
			should_cont = False
			break

	return all_tracks

def get_genre_list(song_title, album_name):
    metadata = pygn.search(clientID=pgyn_clientID, userID=pgyn_userID, track=song_title, album=album_name)

    if not metadata:
        # print 'Unknown Error'
        return None
    elif 'genre' in metadata:
        genre_list = []

        genre_data = metadata['genre']
        for gi in genre_data:
            genre_text = genre_data[gi]['TEXT']
            genre_list += [genre_text]

        return genre_list
    else:
        # print 'No Genre Error'
        # print metadata
        return None

def map_track_to_genre(track_data):
	output =  get_genre_list(track_data['title'], track_data['album'])
	return output

def filter_exclude_empty_list(item_list):
	if len(item_list) > 0:
		return True
	else:
		return False

def map_first_list_item(item_list):
	return item_list[0]

def generate_library_description(single_track_genres):
	genre_freq=collections.Counter(single_track_genres)
	most_common = genre_freq.most_common(5)

	return "You listen to mostly {} with a little bit of {}, {}, and {}".format(
		most_common[0][0],
		most_common[1][0],
		most_common[2][0],
		most_common[3][0]
		)

def describe_songs(access_data):
	# load from cache/pickle if possible
	all_tracks = load_track_list(access_data)

	subset_tracks = random.sample(all_tracks, min(len(all_tracks), 60))

	pool = multiprocessing.Pool(15)
	raw_track_genres = pool.map(map_track_to_genre, subset_tracks)
	valid_track_genres = filter(filter_exclude_empty_list, raw_track_genres)
	single_track_genres = map(map_first_list_item, valid_track_genres)
	return generate_library_description(single_track_genres)

# if __name__ == '__main__':
# 	# use user_profile to lookup access_data and track data
# 	access_data = load_oauth_access_data() # <= user_profile
# 	print describe_songs(access_data)
