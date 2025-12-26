"""
Filename: Sentiment.py

Description:
    Supports query-based searches, optional phrase filtering, 
    pagination via cursors, and configurable result limits. Performs
    sentiment analysis on tweets base off of a user query and phrase  
    using a HuggingFace model.

Author: Rahul Pothineni
Created: 2025-12-05 - Present

Dependencies:
    - requests
    - transformers


##########
This project uses a pretrained transformer-based sentiment analysis model
from Hugging Face:

- **Model:** `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Authors:** Cardiff NLP
- **Source:** https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
- **License:** MIT License

The model is used to analyze sentiment in Twitter/X posts related to NFL players.
No model weights were modified or retrained in this project.
##########

"""

import Database
import Extract
import requests
import statistics
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from PlayerRAG import PlayerRAG

RAPIDAPI_KEY = Extract.RAPIDAPI_KEY
RAPIDAPI_HOST = Extract.RAPIDAPI_HOST

BASE_URL = f"https://{RAPIDAPI_HOST}/search.php"

#Load the sentiment model
tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")
model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")

# Initialize RAG
rag = PlayerRAG()

def analyze_twitter_sentiment(
    query: str,
    phrase: str = "",
    limit: int = 1000,
    search_type: str = "Top"
):
    """
    Searches Twitter using twitter-api45 and runs sentiment analysis
    """

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    sentiment_task = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    polarities = [] # list of polarites for all tweets
    analyzed_count = 0 # amount of tweets analyzed
    cursor = None # pragmentation cursor
    phrase_lower = phrase.lower() #consistency 

    # Resolve player using Claude (synchronous, no async needed)
    player_info = rag.retrieve_player_info(query)
    if not player_info:
        print(f"Could not resolve player: {query}")
        return
    
    # Insert/get player
    player_id = Database.insert_player(
        player_info["name"],
        player_info["team"],
        player_info["position"]
    )

    while analyzed_count < limit:
        params = {
            "query": player_info["name"],  # Search for actual player name, not the nickname
            "search_type": search_type
        }

        if cursor:
            params["cursor"] = cursor

        # making an http get request 
        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        try:
            data = response.json()
        except Exception:
            print("Failed to parse response")
            break
        
        # filling tweets list
        tweets = Extract.extract_tweets(data)

        if not tweets:
            break
        
        # anylzing tweets one by one 
        for tweet in tweets:
            if analyzed_count >= limit:
                break
            
            # move to the next tweet if the current one isn't parsable
            if not isinstance(tweet, dict):
                continue
            
            text = Extract.extract_text(tweet)

            if not text:
                continue
            
            # checks if the user phrase is in the tweet, if not move to the next tweet
            if phrase_lower and phrase_lower not in text.lower():
                continue
            
            # creates sentiment for the tweet.
            # sentiment comes out from the model like this: [{'label': 'Negative', 'score': 0.7236}],
            # so we grab the "score" aka our sentiment score and the sign of the sentiment from "label"
            sentiment_temp_dict = sentiment_task(text)
            if(sentiment_temp_dict[0]["label"].lower() == "negative"):
                sentiment = -sentiment_temp_dict[0]["score"]
            else: sentiment = sentiment_temp_dict[0]["score"]

            polarities.append(sentiment)
            analyzed_count += 1

            print("TWEET:")
            print(text)
            print()
            print("Polarity:", sentiment)
            print("-" * 60)

            # call to insert tweet into the db
            Database.insert_tweet(text, sentiment, "  ", player_id)

        # checks if there is anymore data from the next page (pagination cursor)
        cursor = Extract.extract_cursor(data)
        if not cursor:
            break

    if analyzed_count == 0:
        print(f"No tweets found for query='{query}' containing '{phrase}'")
        return

    avg_polarity = statistics.mean(polarities)

    positive = sum(1 for p in polarities if p > 0.1)
    negative = sum(1 for p in polarities if p < -0.1)
    neutral = analyzed_count - positive - negative

    print("\n===== SUMMARY =====")
    print(f"Query: {query}")
    print(f"Phrase filter: '{phrase}'")
    print(f"Search type: {search_type}")
    print(f"Tweets analyzed: {analyzed_count}")
    print(f"Average polarity: {avg_polarity:.3f}")
    print(f"Positive: {positive}")
    print(f"Negative: {negative}")
    print(f"Neutral:  {neutral}")

    # returns a summary dict for the API.
    return{
        "tweets_analyzed": analyzed_count,
        "average_polarity": avg_polarity,
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    }