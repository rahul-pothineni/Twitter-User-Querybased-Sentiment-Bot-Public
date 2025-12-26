"""
Twitter Sentiment Analysis API (FastAPI)

Author: Rahul Pothineni
Description:
    This module defines a FastAPI application that exposes an endpoint
    for analyzing Twitter sentiment related to NFL players.

    The API accepts a user-provided player query, resolves the player
    using a retrieval-augmented generation (RAG) system, analyzes recent
    tweets using a sentiment analysis pipeline, and returns aggregated
    sentiment statistics including polarity scores and sentiment counts.
Date: 2025-12-25 - Present

Endpoints:
    POST /analyze_sentiment
        - Resolves an NFL player name
        - Runs Twitter sentiment analysis
        - Returns structured sentiment metrics

    GET /
        - Health / welcome endpoint

Dependencies:
    - FastAPI
    - Pydantic
    - PlayerRAG
    - Sentiment
    - Database

Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# import project classes
from PlayerRAG import PlayerRAG
import Sentiment
import Database

app = FastAPI(
    title="Twitter Sentiment Analysis API",
    description="An API to analyze the sentiment of tweets for NFL players.",
    version="1.0.0"
)

# load RAG once instead of every call to the API
rag = PlayerRAG()

# expected request to the API
class PlayerQueryRequest(BaseModel):
    user_name_query: str
    phrase_filter: str = ""
    tweets_run: int = 10

# expected response from the API
class PlayerQueryResponse(BaseModel):
    player_name: str
    tweets_analyzed: int
    average_polarity: float
    positive: int
    negative: int
    neutral: int


@app.post("/analyze_sentiment", response_model=PlayerQueryResponse)
def analyze_sentiment(request: PlayerQueryRequest):
    print(f"Received request to analyze sentiment for player: {request.user_name_query}")

    # try to find player using the RAG system
    player_info = rag.retrieve_player_info(request.user_name_query)
    query_name = request.user_name_query.strip()

    # if player not found, raise 404 not found error
    if not player_info:
        player_info = rag.retrieve_player_info(query_name.title())
    if not player_info:
        player_info = rag.retrieve_player_info(query_name.upper())
    if not player_info:
        print("RAG returned:", player_info)
        raise HTTPException(status_code=404, detail=f"Could not find player: {request.user_name_query}")
    
    # insert player into database
    player_id = Database.insert_player(
        gov_name = player_info["name"],
        team = player_info["team"],
        position = player_info["position"]
    )
    # analyze sentiment using existing function
    sentiment_summary = Sentiment.analyze_twitter_sentiment(
        query = player_info["name"],
        phrase = request.phrase_filter,
        limit = request.tweets_run,
    )

    # if the Twitter API could not find any tweets, raise 404 error
    if not sentiment_summary:
        raise HTTPException(
            status_code=404,
            detail="Sentiment analysis failed. No tweets found for specified player."
        )
    return PlayerQueryResponse(
        player_name = player_info["name"],
        tweets_analyzed = sentiment_summary["tweets_analyzed"],
        average_polarity = sentiment_summary["average_polarity"],
        positive = sentiment_summary["positive"],
        negative = sentiment_summary["negative"],
        neutral = sentiment_summary["neutral"]
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Twitter Sentiment Analysis API. Use the /analyze_sentiment endpoint to analyze player sentiment."}