from zotify.const import ITEMS, ID, TRACK, NAME, ADDED_AT, ARTISTS, ALBUM
from zotify.termoutput import Printer, PrintChannel
from zotify.track import download_track, save_missing_song
from zotify.utils import split_input
from zotify.zotify import Zotify

MY_PLAYLISTS_URL = 'https://api.spotify.com/v1/me/playlists'
PLAYLISTS_URL = 'https://api.spotify.com/v1/playlists'


def get_all_playlists():
    """ Returns list of users playlists """
    playlists = []
    limit = 50
    offset = 0

    while True:
        resp = Zotify.invoke_url_with_params(MY_PLAYLISTS_URL, limit=limit, offset=offset)
        offset += limit
        playlists.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return playlists


def get_playlist_songs(playlist_id):
    """ returns list of songs in a playlist """
    songs = []
    offset = 0
    limit = 100

    while True:
        resp = Zotify.invoke_url_with_params(f'{PLAYLISTS_URL}/{playlist_id}/tracks', limit=limit, offset=offset)
        offset += limit
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return songs


def get_playlist_info(playlist_id):
    """ Returns information scraped from playlist """
    (raw, resp) = Zotify.invoke_url(f'{PLAYLISTS_URL}/{playlist_id}?fields=name,owner(display_name)&market=from_token')
    return resp['name'].strip(), resp['owner']['display_name'].strip()


def download_playlist(playlist):
    """Downloads all the songs from a playlist"""

    playlist_songs = [song for song in get_playlist_songs(playlist[ID]) if song[TRACK][ID]]
    p_bar = Printer.progress(playlist_songs, unit='song', total=len(playlist_songs), unit_scale=True)
    enum = 1
    char_num = len(str(len(playlist_songs)))
    for song in p_bar:
        if song[TRACK][ID]:
            download_track('extplaylist', song[TRACK][ID], extra_keys={'playlist': playlist[NAME], 'playlist_added_at': song[ADDED_AT], 'playlist_num': str(enum).zfill(2)}, disable_progressbar=True)
            p_bar.set_description(song[TRACK][NAME])
        elif song[TRACK][NAME]:
            Printer.print(PrintChannel.SKIPS, '###   SKIPPING:  SONG DOES NOT EXIST ANYMORE (INFO SAVED)   ###' + "\n")
            save_missing_song('playlist', song[TRACK][NAME], song[TRACK][ARTISTS][0][NAME], song[TRACK][ALBUM][NAME], extra_keys=
            {
                'playlist_song_name': song[TRACK][NAME],
                'playlist_added_at': song[ADDED_AT],
                'playlist': playlist[NAME],
                'playlist_num': str(enum).zfill(char_num),
                'playlist_id': playlist[ID],
                'playlist_track_id': ""
            })
        else:
            Printer.print(PrintChannel.SKIPS, '###   SKIPPING:  SONG DOES NOT EXIST ANYMORE (INFO SAVED)   ###' + "\n")
        enum += 1


def download_from_user_playlist():
    """ Select which playlist(s) to download """
    playlists = get_all_playlists()

    count = 1
    for playlist in playlists:
        print(str(count) + ': ' + playlist[NAME].strip())
        count += 1

    selection = ''
    print('\n> SELECT A PLAYLIST BY ID')
    print('> SELECT A RANGE BY ADDING A DASH BETWEEN BOTH ID\'s')
    print('> OR PARTICULAR OPTIONS BY ADDING A COMMA BETWEEN ID\'s\n')
    while len(selection) == 0:
        selection = str(input('ID(s): '))
    playlist_choices = map(int, split_input(selection))

    for playlist_number in playlist_choices:
        playlist = playlists[playlist_number - 1]
        print(f'Downloading {playlist[NAME].strip()}')
        download_playlist(playlist)

    print('\n**All playlists have been downloaded**\n')
