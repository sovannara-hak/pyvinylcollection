import sqlbrowser
import sqlite3
import os.path
import discogsParse
import json

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
		super(MyApp, self).__init__(*args)

	def main(self, name='VinylCollection'):
		self.mainWindow = gui.HBox(width='100%', height='100%')

		self.leftLayout = gui.VBox(width=350, height='100%')

		self.wid = gui.VBox(width=350, height='90%')
		self.wid.style['display'] = 'block'
		self.wid.style['overflow'] = 'auto'
		  
		self.filterInput = gui.TextInput(width=200, height=20, margin='10px')
		self.filterInput.set_on_enter_listener(self.on_filter_input_enter)
		self.generateReleaseTree(self.wid)
		self.syncButton = gui.Button("Sync", width=200, height=30, margin='10px')
		self.syncButton.set_on_click_listener(self.on_sync_pushed)

		# returning the root widget
		self.leftLayout.append(self.filterInput)
		self.leftLayout.append(self.wid)
		self.leftLayout.append(self.syncButton)

		self.rightLayout = gui.VBox(width='100%', height='100%')

		self.mainWindow.append(self.leftLayout)
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

			self.mainWindow.append(rightLayout, key='rightLayout')
				

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
            start(MyApp, debug=True, address='0.0.0.0', update_interval=0.3)
            #start(MyApp, standalone=True)
