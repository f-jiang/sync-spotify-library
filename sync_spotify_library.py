from os import environ
from time import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth


REQUEST_LIST_MAX_LEN = 50


def _get_all_items(result):
    assert isinstance(result, dict) and {'previous', 'items', 'next'} < result.keys()

    items = result['items']

    while result['next']:
        result = sp.next(result)
        items += result['items']

    return items


def _get_all_track_ids():
    tracks = []

    playlists = _get_all_items(sp.current_user_playlists())
    for i, playlist in enumerate(playlists):
        playlist_id = playlist['id']
        playlist_tracks_with_date = _get_all_items(sp.user_playlist_tracks(playlist_id=playlist_id))
        playlist_tracks = [t['track'] for t in playlist_tracks_with_date]
        tracks += playlist_tracks
        print('added {} tracks from playlist {} of {}'.format(len(playlist_tracks),
                                                              i + 1,
                                                              len(playlists)))

    albums = _get_all_items(sp.current_user_saved_albums())
    for i, album in enumerate(albums):
        album_id = album['album']['id']
        album_tracks = _get_all_items(sp.album_tracks(album_id))
        tracks += album_tracks
        print('added {} tracks from album {} of {}'.format(len(album_tracks),
                                                           i + 1,
                                                           len(albums)))

    return list(set(t['id'] for t in tracks if t['id']))


def _split_list(l, sublist_len):
    for i in range(0, len(l), sublist_len):
        yield l[i:min(i + sublist_len, len(l))]


if __name__ == '__main__':
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=environ.get('CLIENT_ID'),
                                                   client_secret=environ.get('CLIENT_SECRET'),
                                                   redirect_uri="http://localhost:8080",
                                                   scope=['user-library-modify',
                                                          'user-library-read']))

    start_time = time()

    track_ids = _get_all_track_ids()
    print('total of', len(track_ids), 'unique tracks in playlists and saved albums')

    saved_track_ids = set(t['track']['id'] for t in get_all_items(sp.current_user_saved_tracks()))
    track_ids_to_remove = list(saved_track_ids - set(track_ids))
    print(len(track_ids_to_remove), 'saved tracks to remove (not in playlists or saved albums)')
    for sublist in _split_list(track_ids_to_remove, REQUEST_LIST_MAX_LEN):
        sp.current_user_saved_tracks_delete(sublist)

    track_in_saved = []
    for sublist in _split_list(track_ids, REQUEST_LIST_MAX_LEN):
        track_in_saved += sp.current_user_saved_tracks_contains(sublist)
    track_ids_to_add = [track_ids[i] for i in range(len(track_ids)) if not track_in_saved[i]]
    print(len(track_ids_to_add), 'tracks to save')
    for sublist in _split_list(track_ids_to_add, REQUEST_LIST_MAX_LEN):
        sp.current_user_saved_tracks_add(sublist)

    print('total runtime:', time() - start_time, 's')

