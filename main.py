# Import necessary modules
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# Initialse Flask App
app = Flask(__name__)

# Set name of session cookie
app.config['Session_Cookie_Name'] = 'Spotify Cookie'

# Set a random secret key to sign the cookie
app.secret_key = 'leelicious'

# Set the key for the token info in the session dictionary
Token_Info = 'token_info'

# Route to handle logging in
@app.route('/')
def login():
    # Create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # Redirect the user to the authorization URL
    return redirect (auth_url)

# Route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # Clear the session
    session.clear()
    # Get the authorization code from the request parameters
    code = request.args.get('code')
    # Exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # Save the token info in the session
    session[Token_Info] = token_info
    # Redirect the user to the save_discover_weekly route
    return redirect(url_for('save_discover_weekly', _external = True))

# Route to save the Discover Weekly songs to a playlist
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        # Get the token info from the session
        token_info = get_token()
    except:
        # If the token info is not found, redirect the user to the login route
        print("User not logged in")
        return redirect("/")

    # Create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get the user's playlists
    current_playlists = sp.current_user_playlists()['items']
    user_id = sp.current_user()['id']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # Find the Discover Weekly and Saved Weekly playlists
    for playlist in current_playlists:
        if(playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']

    # If the Discover Weekly playlist is not found, return an error message
    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found'
    
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    # Get the tracks from the Discover Weekly playlist
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    
    # Add the tracks to the Saved Weekly playlist
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    # Return a success message
    return ("SUCCESS!!")

# Function to get the token info from the session
def get_token():
    token_info = session.get(Token_Info, None)
    # If the token info is not found, redirect the user to the login route
    if not token_info:
        redirect(url_for('login', _external = False))

    # Check if the token is expired and refresh it if necessary
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
