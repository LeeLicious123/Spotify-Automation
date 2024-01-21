import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

app = Flask(__name__)

app.config['Session_Cookie_Name'] = 'Spotify Cookie'
app.secret_key = 'leelicious'
Token_Info = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect (auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[Token_Info] = token_info
    return redirect(url_for('save_discover_weekly', _external = True))

@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")

    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_playlists = sp.current_user_playlists()['items']
    user_id = sp.current_user()['id']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    for playlist in current_playlists:
        if(playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found'
    
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    return ("SUCCESS!!")

def get_token():
    token_info = session.get(Token_Info, None)
    if not token_info:
        redirect(url_for('login', _external = False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = "6482c5322b5043e7b46bd459d2333572",
        client_secret = "343a630bdd874098921103e6bd284270",
        redirect_uri = url_for('redirect_page', _external= True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private')

app.run(debug=True)
