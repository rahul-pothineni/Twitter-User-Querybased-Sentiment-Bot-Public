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



def get_player_id_by_name(PlayerName):
    """Get PlayerID by GovName"""
    result = conn.execute(
        "SELECT PlayerID FROM Players WHERE GovName = ?",
        (PlayerName,)
    ).fetchone()
    return result[0] if result else None


def insert_player(GovName, Team, Position):
    """Insert player, avoiding duplicates"""
    try:
        cur.execute(
            "INSERT INTO Players (GovName, Team, Position) VALUES (?, ?, ?);",
            (GovName, Team, Position)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        print(f"Player '{GovName}' already exists")
        return get_player_id_by_name(GovName)


def insert_tweet(TweetText, SentimentScore, DateTimeCreated, PlayerID):
    """Insert tweet and sentiment data into the database"""

    cur.execute("INSERT INTO Tweets (TweetText, DateTimeCreated, PlayerID) VALUES (?, ?, ?);", (TweetText, DateTimeCreated, PlayerID))
    TweetID = cur.lastrowid
    cur.execute("INSERT INTO Sentiment (PlayerID, TweetID, SentimentScore) VALUES (?, ?, ?);", (PlayerID, TweetID, SentimentScore))
    conn.commit()


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
