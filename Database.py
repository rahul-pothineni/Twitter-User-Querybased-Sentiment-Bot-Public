"""
Filename: Database.py

Description:
    Manages SQLite database for storing NFL player data, tweets, and sentiment scores.
    Handles player insertion with duplicate prevention, tweet storage, and sentiment
    analysis results. Provides a view for querying combined sentiment and tweet data.

Author: Rahul Pothineni
Created: 2025-12-17 - Present

Dependencies:
    - sqlite3
"""

import sqlite3
DB_PATH = "tweets.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
conn.commit()
cur = conn.cursor()


# create tables
cur.executescript("""
CREATE TABLE IF NOT EXISTS Players (
    PlayerID INTEGER PRIMARY KEY AUTOINCREMENT ,
    GovName TEXT NOT NULL UNIQUE,
    Team TEXT NOT NULL,
    Position TEXT NOT NULL );
            
CREATE TABLE IF NOT EXISTS Tweets ( 
    TweetID INTEGER PRIMARY KEY AUTOINCREMENT, 
    TweetText TEXT NOT NULL, 
    DateTimeCreated TEXT NOT NULL, 
    PlayerID INTEGER,
    FOREIGN KEY (PlayerID) REFERENCES Players (PlayerID) );
            
CREATE TABLE IF NOT EXISTS Sentiment (
    PlayerID INTEGER,
    TweetID INTEGER,
    SentimentScore REAL NOT NULL, 
    PRIMARY KEY (PlayerID, TweetID),
    FOREIGN KEY (PlayerID) REFERENCES Players (PlayerID),
    FOREIGN KEY (TweetID) REFERENCES Tweets (TweetID) );

""")



def get_player_id_by_name(player_name):
    """Get PlayerID by GovName (normalized)"""

    name = player_name.strip().lower()
    result = conn.execute(
        "SELECT PlayerID FROM Players WHERE LOWER(TRIM(GovName)) = ?",
        (name,)
    ).fetchone()
    return result[0] if result else None


def insert_player(gov_name, team, position):
    """Insert player if not exists, return existing PlayerID if duplicate"""

    # Normalize input
    name = gov_name.strip()
    team = team.strip()
    position = position.strip()
    
    # Check if player already exists in the db
    player_id = get_player_id_by_name(name)
    
    if player_id:
        return player_id
    
    # Insert new player
    try:
        cur.execute(
            "INSERT INTO Players (GovName, Team, Position) VALUES (?, ?, ?);",
            (name, team, position)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        # Fallback if still fails
        print(f"Player '{name}' insertion failed")
        return get_player_id_by_name(name)


def insert_tweet(tweet_text, sentiment_score, date_time_created, player_id):
    """Insert tweet and sentiment data into the database"""

    cur.execute(
        "INSERT INTO Tweets (TweetText, DateTimeCreated, PlayerID) VALUES (?, ?, ?);",
        (tweet_text, date_time_created, player_id)
    )

    # Gets the last row id of the tweet inserted, which is autoincremented. 
    # Nedded when inserting into the Sentiment table as it needs the TweetID. 
    tweet_id = cur.lastrowid
    cur.execute(
        "INSERT INTO Sentiment (PlayerID, TweetID, SentimentScore) VALUES (?, ?, ?);",
        (player_id, tweet_id, sentiment_score)
    )
    conn.commit()

# used for debugging. 
def print_sentiment_and_tweets():
    """Create and print a view that combines Sentiment, Players, and Tweets tables"""

    cur.execute("""
    CREATE VIEW IF NOT EXISTS SentimentView AS
    SELECT
        s.PlayerID,
        p.GovName,
        s.TweetID,
        t.TweetText,
        t.DateTimeCreated,
        s.SentimentScore
    FROM Sentiment s
    LEFT JOIN Players p ON s.PlayerID = p.PlayerID
    LEFT JOIN Tweets t ON s.TweetID = t.TweetID
    """)                
    for row in cur.execute("SELECT * FROM SentimentView;"):
        print(row)
