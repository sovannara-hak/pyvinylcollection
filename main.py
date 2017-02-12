import sqlbrowser
import sqlite3
import os.path
import discogsParse
import json
import customRelease
from config import *

import remi.gui as gui
from remi import start, App

class ReleaseInfo(object):
	def __init__(self):
		self.title = ""
		self.artistId = ""
		self.discogsId = ""

class TrackInfo(object):
	def __init__(self):
		self.title = ""
		self.artist = ""
		self.duration = ""

class MyApp(App):
	def __init__(self, *args):
                res_path = os.path.join(os.path.dirname(__file__), 'res')
		super(MyApp, self).__init__(*args, static_file_path=res_path)

	def main(self, name='VinylCollection'):
		self.mainWindow = gui.HBox(width='100%', height='100%')

		self.leftLayout = gui.VBox(width=350, height='100%')

		self.wid = gui.VBox(width=350, height='80%')
		self.wid.style['display'] = 'block'
		self.wid.style['overflow'] = 'auto'
		  
		self.filterInput = gui.TextInput(width=200, height=20, margin='10px')
                self.filterInput.attributes['autocomplete'] = 'off'
		self.filterInput.set_on_enter_listener(self.on_filter_input_enter)
		self.generateReleaseTree(self.wid)
		self.syncButton = gui.Button("Sync", width=200, height=30, margin='10px')
		self.syncButton.set_on_click_listener(self.on_sync_pushed)

		# returning the root widget
		self.leftLayout.append(self.filterInput)
		self.leftLayout.append(self.wid)

		self.buttonBar = gui.HBox(width=350, height='10%')
		self.addCustomButton = gui.Button("Add custom release", width=280, height=30, margin='10px')
		self.addCustomButton.set_on_click_listener(self.on_add_custom_pushed)

		self.buttonBar.append(self.addCustomButton)
		self.buttonBar.append(self.syncButton)

		self.leftLayout.append(self.buttonBar)

		self.rightLayout = gui.VBox(width='100%', height='90%')

		self.mainWindow.append(self.leftLayout, key='lefLayout')
		self.mainWindow.append(self.rightLayout, key='rightLayout')

		return self.mainWindow
	
	def on_filter_input_enter(self, widget, newValue):
		filter = self.filterInput.get_value()
		self.generateReleaseTree(self.wid, filter)
		filter = self.filterInput.set_value("")

	def on_sync_pushed(self, widget):
		self.conn = sqlite3.connect('mycollec.db')
                discogsParse.fetchCollection(self.conn, discogs_username)
		self.generateReleaseTree(self.wid)

	def on_add_custom_pushed(self, widget):
		self.custom_release_wid()

	def on_submit_pushed(self, widget):
		self.conn = sqlite3.connect('mycollec.db')
		sqlbrowser.submitScrobble(self.conn)	

	def on_track_checked(self, widget, *userdata):
		self.conn = sqlite3.connect('mycollec.db')
		val = userdata[0]
		trackinfo = userdata[1]
		print trackinfo.artist, trackinfo.title, val
		sqlbrowser.updateScrobbleQueue(self.conn, trackinfo, val)

	def on_release_clicked(self, widget, *userdata):
		self.conn = sqlite3.connect('mycollec.db')
		sqlbrowser.clearScrobbleQueue(self.conn)
		for releaseInfo in userdata:
			rightLayout = gui.VBox(width='100%', height='90%')
			rightLayout.style['display'] = 'block'
			rightLayout.style['overflow'] = 'auto'
			tracksList = sqlbrowser.getTracksList(self.conn, releaseInfo.discogsId)
			for track in tracksList:
				trackInfo = TrackInfo()
				trackInfo.title = track[1]
				trackInfo.duration = track[4]
				trackInfo.artist = track[2]
				
				sqlbrowser.insertIntoScrobbleQueue(self.conn, trackInfo)

				checkBox = gui.CheckBoxLabel(track[5] + " " + track[1], True, width='70%', height=20, margin='10px')
				checkBox.set_on_change_listener(self.on_track_checked, trackInfo)
				rightLayout.append(checkBox)

			submitButton = gui.Button("Submit", width=200, height=30, margin='10px')
			submitButton.set_on_click_listener(self.on_submit_pushed)
			rightLayout.append(submitButton)
			self.rightLayout = rightLayout
			self.mainWindow.append(self.rightLayout, key='rightLayout')
				
	def on_custom_release_add_track(self, widget, *userdata):
		tracklist = gui.HBox(widht=100, height=20)
		tracklistPosition= gui.TextInput(width=30, height=20, margin='10px', single_line=True)
		tracklistArtist= gui.TextInput(width=100, height=20, margin='10px', single_line=True)
		tracklistTitle= gui.TextInput(width=100, height=20, margin='10px', single_line=True)
		tracklist.append(tracklistPosition, key="trackPosition")
		tracklist.append(tracklistArtist, key="trackArtist")
		tracklist.append(tracklistTitle, key="trackTitle")
		userdata[0].append(tracklist)
		return

	def on_custom_add_release(self, widget, *userdata):
		releaseYear = int(userdata[0][0].children["yearTextInput"].get_value())
		releaseArtist = userdata[0][0].children["artistTextInput"].get_value()
		releaseTitle = userdata[0][0].children["titleTextInput"].get_value()
		
		releaseArtistData = customRelease.artists(releaseArtist)	
		tracklist = []

		if len(userdata[0][1].children) == 1:
			return

		for row in userdata[0][1].children.values():
			if "trackPosition" in row.children.keys():
				position = row.children["trackPosition"].get_value()
				artist = row.children["trackArtist"].get_value()
				title = row.children["trackTitle"].get_value()
				
				trackArtistData = None
				if artist != "":
					trackArtistData = customRelease.artists(artist)
				if position != "" and title != "":
					track = customRelease.track(trackArtistData, position, title)
					tracklist.append(track)

		if len(tracklist) > 0:
			release = customRelease.release(releaseYear, releaseArtistData, releaseTitle, tracklist)
			releaseJson = customRelease.get_json(release)

			conn = sqlite3.connect('mycollec.db')
			#Insert dans la table album
			#Insert dans la table track
			print releaseJson
			discogsParse.parseRelease(conn, release)
			self.generateReleaseTree(self.wid)
		return

	def custom_release_wid(self):
		layoutV = gui.VBox(width='80%', height='100%')
		layoutV.style['display'] = 'block'
		layoutV.style['overflow'] = 'auto'
		layoutReleaseInfo = gui.HBox(width='80%', height='10%')
		yearLabel = gui.Label("Year: ", width=20, height=20)
		yearTextInput = gui.TextInput(width=50, height=20, margin='10px', single_line=True)
		artistLabel = gui.Label("Artist: ", width=20, height=20)
		artistTextInput = gui.TextInput(width=200, height=20, margin='10px', single_line=True)
		titleLabel = gui.Label("Title: ", width=20, height=20)
		titleTextInput = gui.TextInput(width=200, height=20, margin='10px', single_line=True)

		layoutReleaseInfo.append(yearLabel, key='yearLabel')
		layoutReleaseInfo.append(yearTextInput, key='yearTextInput')
		layoutReleaseInfo.append(artistLabel, key='artistLabel')
		layoutReleaseInfo.append(artistTextInput, key='artistTextInput')
		layoutReleaseInfo.append(titleLabel, key='titleLabel')
		layoutReleaseInfo.append(titleTextInput, key='titleTextInput')
		
		tracklist = gui.VBox(width='80%', height='70%')
		tracklist.style['display'] = 'block'
		tracklist.style['overflow'] = 'auto'
		tracklistLabel = gui.HBox(widht=100, height=20)
		tracklistPositionLabel = gui.Label("Position", width=30, height=20)
		tracklistArtistLabel = gui.Label("Artist", width=100, height=20)
		tracklistTitleLabel = gui.Label("Title", width=100, height=20)
		tracklistLabel.append(tracklistPositionLabel)
		tracklistLabel.append(tracklistArtistLabel)
		tracklistLabel.append(tracklistTitleLabel)
		tracklist.append(tracklistLabel)

		layoutButton = gui.HBox(width='80%', height=20)
		addTrackButton = gui.Button("Add track")
		addTrackButton.set_on_click_listener(self.on_custom_release_add_track, tracklist)
		addReleaseToDb = gui.Button("Save to database")
		addReleaseToDb.set_on_click_listener(self.on_custom_add_release, [layoutReleaseInfo, tracklist])
		layoutButton.append(addTrackButton)
		layoutButton.append(addReleaseToDb)

		layoutV.append(layoutReleaseInfo)
		layoutV.append(tracklist)
		layoutV.append(layoutButton)
		
		self.rightLayout = layoutV
		self.mainWindow.append(layoutV, key='rightLayout')
		return

				

	def generateReleaseTree(self, wid, filter=""):
		self.conn = sqlite3.connect('mycollec.db')
		tree = gui.TreeView(width=300, height=300)

		artistsList = sqlbrowser.getArtistsList(self.conn, filter)
		for artist in artistsList:
			it = gui.TreeItem(artist[1])
			tree.append(it)
			albumsList = sqlbrowser.getAlbumsList(self.conn, artist[0])
			for album in albumsList:
				year = album[3]
				title = album[1]
				discogsId = album[0]
				artistId = album[2]
				releaseStr = "["+str(year)+"] " + title
				
				releaseInfo = ReleaseInfo()
				releaseInfo.title = title
				releaseInfo.discogsId = discogsId
				releaseInfo.artistId = artistId

				subit = gui.TreeItem(releaseStr)
				subit.set_on_click_listener(self.on_release_clicked, releaseInfo)
				it.append(subit)
		
		wid.append(tree, key='releaseTree')


if __name__ == "__main__":
	# starts the webserver
	# optional parameters
	# start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
        if discogs_username == "" or lastfm_username == "" or lastfm_password_md5 == "" or lastfm_api_key == "" or lastfm_api_secret == "":
            print "Please Edit config.py"
        else:
            dbFileName = "mycollec.db"
            createDataBase = True
            if (os.path.isfile(dbFileName)):
                    createDataBase = False

            conn = sqlite3.connect('mycollec.db')
            if createDataBase:
                    print "Creating database"
                    sqlbrowser.createDatabase(conn)
                    discogsParse.fetchCollection(conn, discogs_username)

            sqlbrowser.clearScrobbleQueue(conn)
            start(MyApp, debug=True, address='0.0.0.0', websocket_timeout_timer_ms=300, multiple_instance=False, update_interval=0.3)
            #start(MyApp, standalone=True)
