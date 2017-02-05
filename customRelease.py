import json

def artists(name):
   return {"name": name}

def track(artist, position, title):
   if artist is None:
       return {"title": title, "position": position, "type_": "track", "duration": ""}
   else:
       return {"title": title, "artists": [artist], "position": position, "type_": "track", "duration": ""}

def release(year, artistsInfo, title, tracklist):
   releaseId = str(year) + artistsInfo["name"] + title
   return {"id": releaseId, "year": year, "artists": [artistsInfo], "title": title, "tracklist": tracklist}

def get_json(data):
   return json.dumps(data)
