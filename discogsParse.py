import re
import sqlite3
import requests

def fetchCollection(bdd, username):
    current_page = 1
    total_pages = 1
    headers = {'User-Agent': 'pyvinylcollection/0.1'}
    cursor = bdd.cursor()
    while current_page <= total_pages:
        url = 'https://api.discogs.com/users/'+username+'/collection/folders/0/releases?page='+str(current_page)
        r = requests.get(url, headers=headers)
        jsondata = r.json()
        total_pages = jsondata['pagination']['pages']
        parseCollection(bdd, jsondata)

        for release in jsondata['releases']:
            releaseId = release['id']
            
            query = "SELECT COUNT(Id) FROM Tracks WHERE AlbumId = ?"
            cursor.execute(query, (releaseId, ))
            checkAlbumCount = cursor.fetchone()[0]

            if (checkAlbumCount == 0):
                url_release = 'https://api.discogs.com/releases/'+str(releaseId)
                req_release = requests.get(url_release, headers=headers)
                jsondata_release = req_release.json()
                parseRelease(bdd, jsondata_release)

        current_page = current_page + 1

    

def fusionArtists(strData):
	result = ""
	nbArtist = len(strData)
	for i in range(nbArtist):
		if (i > 0 and i < nbArtist - 1):
			separator = ", "
		elif (i == 0):
			separator = ""
		elif( i == nbArtist - 1):
			separator = " & "

		name = re.sub(r'\s+\(\d+\)', '', strData[i]['name'])
		result = result + separator + name
	return result

def parseRelease(bdd, strData):
	cursor = bdd.cursor()
	artist = fusionArtists(strData['artists'])
	year = strData['year']
	title = strData['title']
        discogsID = strData['id']
	
	#print artist + "\n"
	#print "[" + str(year) + " - " + title + "]\n" 
	for track in strData['tracklist']:
		if ('artists' in track.keys()):
			trackArtist = fusionArtists(track['artists'])
		else:
			trackArtist = artist

		#print trackArtist + "\n"
		#print track['position'] + " - " + track['title'] + "\n"

		query = "SELECT COUNT(Id) FROM Artists WHERE Name = ?"
		cursor.execute(query, (artist,));
		checkArtistId = cursor.fetchone()[0]
		if( checkArtistId == 0 ):
			query = "INSERT INTO Artists (Name) VALUES(?)"
			cursor.execute(query, (artist,))

		query = "SELECT Id FROM Artists WHERE Name = ?"
		cursor.execute(query, (artist,))
		artistId = cursor.fetchone()[0]
                
		query = "SELECT COUNT(DiscogsId) FROM Albums WHERE DiscogsId = ?"
		cursor.execute(query, (discogsID, ))
		checkAlbumCount = cursor.fetchone()[0]
		if (checkAlbumCount == 0):
			query = """INSERT INTO `Albums` (`DiscogsId`, `Title`, `ArtistId`, `Year`)
						VALUES(?, ?, ?, ?)"""
			cursor.execute(query, (discogsID, title, artistId, year))

		query = "SELECT DiscogsId FROM Albums WHERE Title = ? AND ArtistId = ?"
		cursor.execute(query, (title, artistId,))
		albumId = cursor.fetchone()[0]


		query = "SELECT COUNT(Id) FROM Tracks WHERE Title = ? AND AlbumArtistId = ? AND AlbumId = ?"
		cursor.execute(query, (track['title'], artistId, albumId,))
		checkTrack = cursor.fetchone()[0]
	
		if (checkTrack == 0 and track['type_'] != "heading"):
			query = """INSERT INTO Tracks (Title, Artist, AlbumArtistId, Position, AlbumId, Length) 
					VALUES(?, ?, ?, ?, ?, ?)"""
			cursor.execute(query, (track['title'], trackArtist, artistId, track['position'], albumId, track['duration']))
			#print "Insert " + track['title'] + "\n"
                #else:
                #    print "heading or exist"
	bdd.commit()

def parseCollection(bdd, strData):
	cursor = bdd.cursor()
	progress = float(strData['pagination']['page']) / float(strData['pagination']['pages'])
	for release in strData['releases']:
		artist = fusionArtists(release['basic_information']['artists'])
		year = release['basic_information']['year']
		albumTitle = release['basic_information']['title']
		discogsID = release['basic_information']['id']

		query = "SELECT COUNT(Id) FROM Artists WHERE Name = ?"
		cursor.execute(query, (artist,))
		checkArtistCount = cursor.fetchone()[0]
		if (checkArtistCount == 0):
			query = "INSERT INTO `Artists` (`Name`) VALUES(?)"
			cursor.execute(query, (artist,))
			#print "Insert " + artist + "\n\n"

		query = "SELECT Id FROM Artists WHERE Name = ?"
		cursor.execute(query, (artist,))
		artistId = cursor.fetchone()[0]

		query = "SELECT COUNT(DiscogsId) FROM Albums WHERE DiscogsId = ?"
		cursor.execute(query, (discogsID, ))
		checkAlbumCount = cursor.fetchone()[0]
		if (checkAlbumCount == 0):
			query = """INSERT INTO `Albums` (`DiscogsId`, `Title`, `ArtistId`, `Year`)
						VALUES(?, ?, ?, ?)"""
			cursor.execute(query, (discogsID, albumTitle, artistId, year))

	bdd.commit()
	return progress

