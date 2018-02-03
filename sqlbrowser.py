import sqlite3
import pylast
import time
from config import *

def fetchCollection(connection):
	res = []
	cursor = connection.cursor()
	query = """SELECT Artists.Name, Albums.Year, Albums.Title, Albums.DiscogsId FROM
		Albums INNER JOIN Artists ON Artists.Id = Albums.ArtistId"""
	cursor.execute(query)
	res = cursor.fetchall()
	return res

def getArtistsList(connection, filter=""):
	res = []
	try:
		cursor = connection.cursor()
		query = ""
		if filter == "":
			query = """SELECT * FROM Artists ORDER BY Name"""
			cursor.execute(query)
		else:
			query = """SELECT * FROM Artists WHERE Name LIKE ? ORDER BY Name"""
			cursor.execute(query, ("%"+filter+"%",))

		res = cursor.fetchall()
	except sqlite3.Error, e:
		print "Error %s:" % e.args[0]

	return res

def getAlbumsList(connection, artistId):
	res = []
	try:
		cursor = connection.cursor()
		query = """SELECT * FROM Albums WHERE ArtistId = ? ORDER BY Year"""
		cursor.execute(query, (artistId,))
		res = cursor.fetchall()
	except sqlite3.Error, e:
		print "Error %s:" % e.args[0]
	return res

def getTracksList(connection, discogsId):
	res = []
	try:
		cursor = connection.cursor()
		query = """SELECT * FROM Tracks WHERE AlbumId = ? ORDER BY CAST(Position AS INTEGER)"""
		cursor.execute(query, (discogsId,))
		res = cursor.fetchall()
	except sqlite3.Error, e:
		print "Error %s:" % e.args[0]
	return res

def getAlbumName(connection, discogsId):
    res = []
    try:
	res = []
	cursor = connection.cursor()
	query = """SELECT Albums.Title FROM
		Albums INNER JOIN Artists ON Artists.Id = Albums.ArtistId
                WHERE Albums.DiscogsId = ? LIMIT 1"""
	cursor.execute(query, (discogsId,))
	res = cursor.fetchall()
    except sqlite3.Error, e:
	print "Error %s:" % e.args[0]
    return res


def clearScrobbleQueue(connection):
	cursor = connection.cursor()
	cursor.execute("DELETE FROM ScrobbleQueue;")
	connection.commit()

def createDatabase(conn):
	cursor = conn.cursor()
        cursor.execute('PRAGMA encoding="UTF-8";')
	
	query = """CREATE TABLE IF NOT EXISTS 
			Artists (`Id` INTEGER PRIMARY KEY AUTOINCREMENT,
				`Name` VARCHAR(240));"""
	cursor.execute(query)

	query = """CREATE TABLE IF NOT EXISTS 
			Albums (DiscogsId VARCHAR(20) PRIMARY KEY,
				Title VARCHAR(240) NOT NULL,
				ArtistId INT(20) NOT NULL,
				Year INTEGER );"""
	cursor.execute(query)

	query = """CREATE TABLE IF NOT EXISTS 
			Tracks (`Id` INTEGER PRIMARY KEY AUTOINCREMENT,
				`Title` VARCHAR(240) NOT NULL,
				`Artist` VARCHAR(240) NOT NULL,
				`AlbumArtistId` INT(20) NOT NULL,
				`Length` VARCHAR(8),
				`Position` VARCHAR(10),
				`AlbumId` VARCHAR(20));"""

	cursor.execute(query)

	query = """CREATE TABLE IF NOT EXISTS 
			ScrobbleQueue (`Id` INTEGER PRIMARY KEY AUTOINCREMENT,
				`Scrobble` INTEGER NOT NULL,
				`Title` VARCHAR(240) NOT NULL,
				`Artist` VARCHAR(240) NOT NULL,
                                `Album` VARCHAR(240) NOT NULL,
				`Length` VARCHAR(8));"""
	cursor.execute(query)
	conn.commit()

def updateScrobbleQueue(conn, trackInfo, bool):
	cursor = conn.cursor()
	query = """UPDATE ScrobbleQueue
		SET Scrobble = ?
		WHERE Artist = ? AND Title = ? AND Album = ?;"""	
	value = 0
	if bool == "true":
		value = 1
	cursor.execute(query, (value, trackInfo.artist, trackInfo.title, trackInfo.album))
	print value
	conn.commit()
	

def insertIntoScrobbleQueue(conn, trackInfo):
	cursor = conn.cursor()
	query = """INSERT INTO ScrobbleQueue(Scrobble, Title, Artist, Album, Length)
			VALUES (?, ?, ?, ?, ?);""" 
	cursor.execute(query, (1, trackInfo.title, trackInfo.artist, trackInfo.album, trackInfo.duration))
	conn.commit()

def submitScrobble(conn):
        network = pylast.LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret,
                username=lastfm_username, password_hash=lastfm_password_md5)
	cursor = conn.cursor()
	query = """SELECT Artist, Title, Album, Length FROM ScrobbleQueue WHERE Scrobble = 1 ORDER BY Id;"""
	cursor.execute(query)
	for row in cursor:
                artist = row[0]
                title = row[1]
                album = row[2]
                timestamp = int(time.time())
                network.scrobble(artist=artist, title=title, album=album, timestamp=timestamp)
		print "[" + row[3] + "] " + row[0] + " - " + row[1] + " - " + row[2]
                #print "Scrobbling..."

def deleteRelease(conn, releaseInfo):
	print releaseInfo.discogsId, releaseInfo.artistId
	cursor = conn.cursor()
	queryDelTracks = """DELETE FROM Tracks WHERE AlbumId = ?"""
	cursor.execute(queryDelTracks, (releaseInfo.discogsId,))

	queryDelAlbum = """DELETE FROM Albums WHERE DiscogsId = ?"""
	cursor.execute(queryDelAlbum, (releaseInfo.discogsId,))

	queryCountAlbum = """SELECT COUNT(*) FROM Albums WHERE ArtistId = ?"""
	cursor.execute(queryCountAlbum, (releaseInfo.artistId,))
	numberOfAlbums = cursor.fetchone()[0]
	if (numberOfAlbums == 0):
		queryDelArtist = """DELETE FROM Artists WHERE Id = ?"""
		cursor.execute(queryDelArtist, (releaseInfo.artistId,))
	conn.commit()

