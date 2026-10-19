#!/usr/bin/env python -t
###############################################################################
#
# File:         itunes.py
# RCS:          $Header: $
# Description:  Interact with iTunes
# Author:       Jim Randell
# Created:      Thu Jul 16 17:05:53 2009
# Modified:     Sat Oct 20 17:19:04 2012 (Jim Randell) jim.randell@gmail.com
# Language:     Python
# Package:      N/A
# Status:       Experimental (Do Not Distribute)
#
# (C) Copyright 2009, Jim Randell, all rights reserved.
#
###############################################################################
# -*- mode: Python; py-indent-offset: 2; -*-

__author__ = "Jim Randell <jim.randell@gmail.com>"
__version__ = "2012-10-20"

# my first Python script - export iTunes playlist to a directory

import appscript

import sys
import re
import os
import shutil
import mactypes

# separator for playlist folders
SEP = ' > '

# you could set this to os.path.expanduser("~/Music/iTunes/iTunes Music/")
# if you haven't changed your library from the default, and that will save time
# especially if your library is large
MUSIC_LIBRARY = ''

###############################################################################

# string that prefixes action functions
ACTION_PREFIX = 'action_'

def action_help(*args):
  "help - provide help"

  # some tourist info
  prog = os.path.basename(sys.argv[0])
  print "[%s version %s, %s]" % (prog, __version__, __author__)

  # print my doc string
  print globals()[ACTION_PREFIX + 'help'].__doc__

  # and now print all the others
  # find all the 'action_' functions
  for k, v in sorted(globals().iteritems()):
    if not k.startswith(ACTION_PREFIX): continue
    k = k[len(ACTION_PREFIX):]
    if k == 'help': continue
    print v.__doc__

###############################################################################

def itunes_connect():

  app = appscript.app('iTunes')

  # iTunes 10.6.3 breaks compatability with appscript
  try:
    v = app.version()
  except AttributeError:
    # load iTunes using a static glue (dumped from iTunes 10.6.1)
    # I restored iTunes 10.6.1 from Time Machine and then used:
    # appscript.terminology.dump("/Applications/iTunes.app", "iTunesGlue.py")
    # and copied the file to /Library/Python/2.7/site-packages
    # then restored the original iTunes application
    #if self.debug: print("attempting to use static glue to connect to iTunes")
    import iTunesGlue
    app = appscript.app('iTunes', terms=iTunesGlue)
    v = app.version() + " [fudged]"

  print "connected to iTunes version %s" % v
  
  return app

###############################################################################

from math import log10

def file_name(text):
  "file_name - translate text to a suitable file name"

  # (maybe want to do something about non-ascii characters too)
  text = text.lower() # downcase
  text = re.sub(r'\s*[\(\[\{].*[\)\]\}]', '', text) # remove things in brackets
  text = re.sub(r'[\'\&\,\.\(\)\!\/\"\?]', '', text) # remove some characters
  text = re.sub(r'\s+', '_', text) # spaces to underscores
  text = re.sub(r'\W+$', '', text) # remove trailing punctuation

  return text


def export_playlist(playlist, dir = os.curdir, ntracks = 0):
  "export_playlist - export the playlist to <dir> (or .)"

  ntracks = int(ntracks) # arguments are passed as strings

  print 'Exporting: "%s" -> %s' % (playlist_path(playlist), dir)

  # create the directory if necessary
  if not os.path.exists(dir):
    print "Creating directory: %s" % dir
    os.makedirs(dir)

  tracks = playlist.tracks()
  if ntracks == 0: ntracks = len(tracks)
  d = str(1 + int(log10(ntracks)))
  nfmt = '%0' + d + 'd-%s%s'
  pfmt = '[%' + d + 'd] "%s" -> %s'

  for i, track in enumerate(tracks):

    # get the path name
    path = track.location().path

    # determine the file extension
    ext = os.path.splitext(path)[1]

    # work out a suitable track name
    name = nfmt % (i+1, file_name(track.name()), ext)

    print pfmt % (i+1, track.name(), name)

    # copy the file
    shutil.copy(path, os.path.join(dir, name))

    # track limit
    if i+1 >= ntracks > 0: break


def action_export_current_playlist(dir = os.curdir, ntracks = 0):
  "export-current-playlist [<dir> [<ntracks>]] - export the current playlist to <dir> (or .)"

  app = itunes_connect()

  try:
    playlist = app.current_playlist()
  except appscript.reference.CommandError:
    print "Can't get current playlist from iTunes"
    return

  export_playlist(playlist, dir, ntracks)

###############################################################################

def find_playlist(playlists, name, kind = appscript.k.none):
  "find_playlist - find a playlist in a list of playlists"

  # a number indicates a playlist index
  try:
    i = int(name)
  except ValueError:
    pass
  else:
    return playlists[i]

  # search for a playlist by path
  for playlist in playlists:
    if not playlist.special_kind() == kind: continue
    if playlist_path(playlist) == name: return playlist


def action_export_playlist(name, dir = os.curdir, ntracks = 0):
  "export-playlist <playlist> [<dir> [<ntracks>]] - export named playlist to <dir> (or .)"

  app = itunes_connect()
  playlist = find_playlist(app.playlists(), name)
  if playlist:
    export_playlist(playlist, dir, ntracks)
  else:
    print "Can't find playlist: %s" % name

##############################################################################

def playlist_path(playlist):
  "playlist_path - return the path of the playlist"

  path = []
  while True:
    path.insert(0, playlist.name())
    try:
      playlist = playlist.parent()
      kind = playlist.special_kind() # this throws an error if the parent isn't really real
    except appscript.reference.CommandError:
      break

  return SEP.join(path)


def playlist_info(playlist):
  "playlist_info: some additional info about a playlist"

  tracks = len(playlist.tracks())
  tracks = "%dtrk" % tracks

  time = playlist.duration()
  (min, sec) = divmod(time, 60)
  (hr,  min) = divmod(min, 60)
  (day, hr)  = divmod(hr, 24)

  if day > 0:
    time = "%dd%02dh%02dm%02ds" % (day, hr, min, sec)
  elif hr > 0:
    time = "%dh%02dm%02ds" % (hr, min, sec)
  elif min > 0:
    time = "%dm%02ds" % (min, sec)
  else:
    time = "%ds" % sec

  size = float(playlist.size())
  if size > 1e12:
    size = "%.1fTB" % (size / 1e12)
  elif size > 1e9:
    size = "%.1fGB" % (size / 1e9)
  elif size > 1e6:
    size = "%.1fMB" % (size / 1e6)
  elif size > 1e3:
    size = "%.1fKB" % (size / 1e3)
  else:
    size = "%dB" % size

  return " ".join([tracks, time, size])


def action_list_playlists(pattern = None):
  "list-playlists [<pattern>] - list the playlists (that match <pattern>)"

  if pattern: pattern = re.compile(pattern, re.IGNORECASE)

  app = itunes_connect()
  for i, playlist in enumerate(app.playlists()):
    if not playlist.special_kind() == appscript.k.none: continue
    if playlist.name() == "Genius Mixes": continue # TODO: fix this properly
    path = playlist_path(playlist)
    if pattern and not pattern.search(path): continue
    info = playlist_info(playlist)
    print "[%3d] %s (%s)" % (i, path, info)

###############################################################################

def create_folder(app, path):
  "create_folder - return a playlist folder, creating folders as necessary"

  folder = find_playlist(app.playlists(), path, appscript.k.folder)
  if folder: return folder

  # split the path into parent and folder
  parts = path.rpartition(SEP)

  # create the folder
  print "Creating iTunes playlist folder: %s" % parts[2]
  folder = app.make(new = appscript.k.folder_playlist)
  folder.name.set(parts[2])

  # if there is a parent folder move it to there
  if parts[0]:
    parent = create_folder(app, parts[0])
    app.move(folder, to = parent)
  
  # return the newly created playlist
  return folder


def action_import_playlist(path, *files):
  "import-playlist <playlist> <files> - import files to named playlist"

  # turn the playlist path into folder and name
  parts = path.rpartition(SEP)
  (folder, name) = (parts[0], parts[2])

  app = itunes_connect()

  # create a playlist with the chosen name
  print "Creating iTunes playlist: %s" % name
  playlist = app.make(new = appscript.k.playlist)
  playlist.name.set(name)

  # if there is a parent folder, find it (creating if necessary)
  if folder:
    parent = create_folder(app, folder)
    app.move(playlist, to = parent)

  # add the files to the playlist
  if files:
    # turn the files into a list of aliases
    files = [mactypes.Alias(file) for file in files]
    track = app.add(files, to = playlist)

  # show the playlist
  app.reveal(playlist)

###############################################################################

def music_library():
  "music_library: find the iTunes Music Library"

  global MUSIC_LIBRARY # stop Python thinking this is a local

  if not MUSIC_LIBRARY:

    # a bit of a nightmare really, we have to read the "Music Folder" key from
    # the property list ~/Music/iTunes/iTunes Music Library.xml

    # fortunately the is a Python helper library to do this for us
    # unfortunately it means parsing a (possibly huge) XML file

    import plistlib
    import urllib

    plist = plistlib.readPlist(os.path.expanduser("~/Music/iTunes/iTunes Music Library.xml"))
    path = urllib.unquote(plist['Music Folder'])

    prefix = 'file://localhost'
    assert(path.startswith(prefix + '/'))
    assert(path.endswith('/'))

    MUSIC_LIBRARY = path[len(prefix):]

  return MUSIC_LIBRARY


def action_remove_playlist(path):
  "remove-playlist <playlist> - remove playlist (and all unattached tracks in it)"

  # BEWARE: this function will remove tracks/files from your iTunes library

  # what we need to do is:
  # 1. get the list of tracks from the playlist (using database_ID)
  # 2. remove the playlist
  # 3. find which tracks are still referenced by other playlists
  # 4. remove any unattached tracks from the Library
  # 5. remove any files belonging to unattached tracks from the Music Folder

  app = itunes_connect()

  # find the playlist
  playlist = find_playlist(app.playlists(), path)
  if not playlist:
    print "Can't find playlist: ", path
    return

  # find the ids of the tracks in this playlist
  tracks = set(x.database_ID() for x in playlist.tracks())

  # delete the playlist itself
  print 'Remove playlist "%s"' % playlist.name()
  app.delete(playlist)

  # now go through each user playlist and remove any tracks contained in other playlists
  for p in app.user_playlists():
    if p.smart(): continue # skip smart playlists
    if not p.special_kind() == appscript.k.none: continue # and other non-normal playlists
    for t in p.tracks():
      tracks.discard(t.database_ID())

  if not tracks: return

  # find the iTunes Music Folder
  dir = music_library()

  # remove the tracks from the iTunes library
  playlist = app.playlists['Library']
  files = []
  for track in playlist.tracks():
    if track.database_ID() in tracks:
      # see if the file is in the music folder
      fn = track.location().path
      if fn.startswith(dir):
        files.append(fn)
      # remove the track from the library
      print 'Remove track "%s" from %s' % (track.name(), playlist.name())
      playlist.delete(track)

  # remove any files marked for deletion
  for fn in files:
    print 'Removing file: %s' % fn
    os.remove(fn)

###############################################################################

def action_play_playlist(path):
  "play-playlist <path> - play the specified playlist in iTunes"

  app = itunes_connect()

  # find the playlist
  playlist = find_playlist(app.playlists(), path)
  if not playlist:
    print "Can't find playlist: ", path
    return

  app.reveal(playlist)
  app.play()


def action_stop():
  "stop - stop playing current track"

  app = itunes_connect()
  app.stop()


def action_play():
  "play - start playing"

  app = itunes_connect()
  app.play()


def action_playpause():
  "playpause - toggle play state"

  app = itunes_connect()
  app.playpause()

###############################################################################

def main(*args):
  space = globals()
  for name in set([args[0], 'help']):
    # determine the corresponding function name
    name = re.sub(r'^-*', '', name) # remove leading hyphens
    name = ACTION_PREFIX + name
    name = re.sub(r'-', '_', name) # map hyphens to underscores

    # if there is an appropriately named function call it
    if name in space:
      fn = space[name]
      if callable(fn):
        return fn(*args[1:])

###############################################################################

if __name__ == "__main__":
  # Python seems to have some problems with character encodings:
  # this seems to work for input/output of non-ascii characters
  enc = sys.stdout.encoding
  if enc == None:
    import locale, codecs
    enc = locale.getdefaultlocale()[1]
    if enc:
      sys.stdout = codecs.getwriter(enc)(sys.stdout)
  # and do the same for command line arguments
  if enc:
    sys.argv = [x.decode(enc) for x in sys.argv]

  # call the appropriate function
  if len(sys.argv) > 1:
    main(*sys.argv[1:])
  else:
    main('help')

###############################################################################
