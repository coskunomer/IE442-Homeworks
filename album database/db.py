import sqlite3
import time
import os
from datetime import datetime, timedelta
import random

# Function to create tables
def create_tables(c):
    # Creating tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS artists (artist_id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS albums (album_id INTEGER PRIMARY KEY, name TEXT, artist_id INTEGER, creation_date DATE, FOREIGN KEY(artist_id) REFERENCES artists(artist_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS songs (song_id INTEGER PRIMARY KEY, title TEXT, duration INTEGER, album_id INTEGER, FOREIGN KEY(album_id) REFERENCES albums(album_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_song_likes (user_id INTEGER, song_id INTEGER, PRIMARY KEY(user_id, song_id), FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(song_id) REFERENCES songs(song_id))''')

# Function to create a database and populate it with fake data
def create_and_populate_database(num_songs):
    conn = sqlite3.connect(f'user_albums_{num_songs}.db')
    c = conn.cursor()

    # Create tables
    create_tables(c)

    # Inserting additional fake data based on the specified number
    for user_id in range(1, num_songs // 25):
        c.execute(f"INSERT INTO users VALUES ({user_id}, 'User {user_id}')")

    for artist_id in range(1, 100):
        c.execute(f"INSERT INTO artists VALUES ({artist_id}, 'Artist {artist_id}')")

    for album_id in range(1, 100):
        # Generate a random date between 2000-01-01 and 2022-01-01
        random_date = (datetime(2000, 1, 1) + timedelta(days=random.randint(0, 8035))).strftime('%Y-%m-%d')
        c.execute(
            f"INSERT INTO albums VALUES ({album_id}, 'Album {album_id}', {album_id % 99 + 1}, '{random_date}')")
    for song_id in range(11, num_songs + 11):
        c.execute(f"INSERT INTO songs VALUES ({song_id}, 'Song {song_id}', 200, {song_id % 10 + 1})")
        c.execute(f"INSERT INTO user_song_likes VALUES ({random.randint(1, num_songs // 25)}, {song_id})")

    # Commit the changes and close connection
    conn.commit()
    conn.close()

# Function to perform the experiment and measure performance
def perform_experiment(num_songs):
    # Create and populate the database
    # UNCOMMENT TO CREATE TABLES
    create_and_populate_database(num_songs)

    # Connect to the database
    conn = sqlite3.connect(f'user_albums_{num_songs}.db')
    c = conn.cursor()

    # Specify the user ID
    user_id = 20

    # Execute the SQL statement and measure performance
    start_time = time.time()
    c.execute('''
        SELECT strftime('%Y', albums.creation_date) AS album_year, songs.title
        FROM songs 
        INNER JOIN albums ON songs.album_id = albums.album_id 
        INNER JOIN user_song_likes ON songs.song_id = user_song_likes.song_id 
        WHERE user_song_likes.user_id = ? 
        GROUP BY strftime('%Y', albums.creation_date), songs.title
    ''', (user_id,))
    years_and_songs = c.fetchall()
    end_time = time.time()
    print(f"Execution Time: {end_time - start_time:.4f} seconds")

    # Print the results and performance
    print(f"Results for {num_songs} songs:")
    print("Years and Songs liked by user:")
    for year, song in years_and_songs:
        print(f"Year: {year}, Song: {song}")

    # Close connection
    conn.close()

# Perform the experiment with different numbers of songs
perform_experiment(100000)
perform_experiment(1000000)
perform_experiment(10000000)

