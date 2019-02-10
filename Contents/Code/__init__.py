import certifi
import requests

VERSION = '4.0'
API_URL = 'http://api.themoviedb.org/3/movie/%s/videos?api_key=%s'
VIDEO_URL = 'http://www.youtube.com/watch?v=%s'
IMAGE_URL = 'https://img.youtube.com/vi/%s/maxresdefault.jpg'

TYPE_ORDER = ['trailer', 'feature_trailer', 'theatrical_trailer', 'behind_the_scenes', 'interview', 'deleted_scene']
TYPE_MAP = {
	"trailer": TrailerObject,
	"behind_the_scenes": BehindTheScenesObject,
	"interview": InterviewObject,
	"deleted_scene": DeletedSceneObject
}

HTTP_HEADERS = {
	"User-Agent": "The Movie Database Trailer/%s (%s %s; Plex Media Server %s)" % (VERSION, Platform.OS, Platform.OSVersion, Platform.ServerVersion)
}

####################################################################################################
def Start():

	pass

####################################################################################################
class TMDBTrailerAgent(Agent.Movies):

	name = 'The Movie Database Trailer'
	languages = [Locale.Language.NoLanguage]
	primary_provider = False
	contributes_to = [
		'com.plexapp.agents.imdb',
		'com.plexapp.agents.themoviedb'
	]

	def search(self, results, media, lang):

		results.Append(MetadataSearchResult(
			id = media.primary_metadata.id,
			score = 100
		))

	def update(self, metadata, media, lang):

		r = requests.get(API_URL % (metadata.id, Prefs['tmdb_api_key']), headers=HTTP_HEADERS, verify=certifi.where())

		if 'status_message' in r.json():
			Log("*** An error occurred: %s ***" % (r.json()['status_message']))
			return None

		extras = []

		for result in r.json()['results']:
			title = result[u'name'].strip()

			if 'tv spot' in title.lower():
				continue

			url = VIDEO_URL % (result[u'key'])
			poster = IMAGE_URL % (result[u'key'])

			# Trailers
			if ('trailer' in title.lower() or result[u'type'].lower() == 'trailer' or result[u'type'].lower() == 'teaser' or result[u'type'].lower() == 'clip') and Prefs['add_trailers']:
				extra_type = 'trailer'

			# Behind the scenes / Featurette
			elif ('behind the scenes' in title.lower() or 'featurette' in title.lower()  or result[u'type'].lower() == 'featurette') and Prefs['add_featurettes']:
				extra_type = 'behind_the_scenes'

			# Interview
			elif 'interview' in title.lower() and Prefs['add_interviews']:
				extra_type = 'interview'

			# Deleted scene
			elif 'deleted scene' in title.lower() and Prefs['add_deleted_scenes']:
				extra_type = 'deleted_scene'

			else:
				continue

			extras.append({
				'type': extra_type,
				'extra': TYPE_MAP[extra_type](
					url = url,
					title = title,
					thumb = poster
				)
			})

		extras.sort(key=lambda e: TYPE_ORDER.index(e['type']))

		for extra in extras:
			metadata.extras.add(extra['extra'])
