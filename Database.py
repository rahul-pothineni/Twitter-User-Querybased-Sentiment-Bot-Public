import sqlite3
DB_PATH = "tweets.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
conn.commit()
cur = conn.cursor()


# create tables
cur.executescript("""
CREATE TABLE Players (
    PlayerID INTEGER PRIMARY KEY AUTOINCREMENT ,
    GovName TEXT NOT NULL,
    Team TEXT NOT NULL,
    Position TEXT NOT NULL );
            
CREATE TABLE Tweets ( 
    TweetID INTEGER PRIMARY KEY AUTOINCREMENT, 
    TweetText TEXT NOT NULL, 
    DateTimeCreated TEXT NOT NULL, 
    PlayerID INTEGER,
    FOREIGN KEY (PlayerID) REFERENCES Players (PlayerID) );
            
CREATE TABLE Sentiment (
    PlayerID INTEGER,
    TweetID INTEGER,
    SentimentScore REAL NOT NULL, 
    PRIMARY KEY (PlayerID, TweetID),
    FOREIGN KEY (PlayerID) REFERENCES Players (PlayerID),
    FOREIGN KEY (TweetID) REFERENCES Tweets (TweetID) );

""")

# Given the PlayerName returns the PlayerID
def get_player_id_by_name(PlayerName):
    return conn.execute(
        "SELECT PlayerID FROM Players WHERE GovName = ?",
        (PlayerName,)
    ).fetchone()

def insert_player(GovName, Team, Position):
    cur.execute("INSERT INTO Players (GovName, Team, Position) VALUES (?, ?, ?);", (GovName, Team, Position))

# Insert a singular tweet into the database in the "Tweet" table, 
# then inserts data for that tweet into the "Sentiment" table. 
def insert_tweet(TweetText, SentimentScore, DateTimeCreated, PlayerName):
    PlayerID = get_player_id_by_name(PlayerName)

    cur.execute("INSERT INTO Tweets (TweetText, DateTimeCreated, PlayerID) VALUES (?, ?, ?);", (TweetText, DateTimeCreated, PlayerID))
    TweetID = cur.lastrowid
    cur.execute("INSERT INTO Sentiment (PlayerID, TweetID, SentimentScore) VALUES (?, ?, ?);", (PlayerID, TweetID, SentimentScore))


#TODO: fix the view; Players db not populating
def print_sentiment_and_tweets():
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
