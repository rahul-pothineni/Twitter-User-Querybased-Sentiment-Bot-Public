"""
Filename: Extract.py

Description:
    Collects tweets using the twitter-api45 RapidAPI endpoint. 
    Includes methods to extract list of tweets from JSON files, 
    individual tweets from the list found in the JSON, and keep 
    track of the pagination cursor.

Author: Rahul Pothineni
Created: 2025-12-05 - Present

Dependencies:
    - requests
"""
import Keys # create own file with api keys (README.md)
import requests
import os

# ==============================
# CONFIG

RAPIDAPI_KEY = Keys.RAPIDAPI_KEY
RAPIDAPI_HOST = Keys.RAPIDAPI_HOST
BASE_URL = f"https://{RAPIDAPI_HOST}/search.php"

# ==============================
# Extraction Methods

def extract_tweets(response_json):
    """
    Twitter-api45 responses vary.
    This tries multiple common locations for tweet lists.
    """
    # if api returns a list then return immediatly 
    if isinstance(response_json, list): 
        return response_json

    # if api does not return a list as checked earlier or a dict then we cannot
    # check it so we return an empty list to throw away
    if not isinstance(response_json, dict):
        return []

    # twitter has no single standard to check tweets so we check all possiblites
    # where the tweet could be
    for key in ["tweets", "timeline", "results", "data", "items"]:

        # look inside the dict json and check if the key exists, if it does
        # then set the retrived value. If it doesn't exist then set the value to
        # None.  
        value = response_json.get(key)

        # we are looking for tweets only which are returned as a list of tweet objects
        if isinstance(value, list):
            return value #function immediately exits when we find a valid searchable list of tweets
    # catch all - no results were found
    return []


def extract_text(tweet):
    '''
    Extracts text from every singular tweet.
    '''
    # check common fields where the tweet text may be stored
    for key in ["text", "full_text", "content", "tweet_text"]:
        value = tweet.get(key)

        # if the the value if text, we know we found the tweet and we return and exit
        if isinstance(value, str) and value.strip():
            return value
    # catch all - no tweet text was found
    return ""


def extract_cursor(response_json):
    '''
    Retrives a token to tell us what page to search on.
    '''

    # The pagination cursor is stored in a dict. 
    if not isinstance(response_json, dict):
        return None

    # check the fields where the cursor may appear
    for key in [
        "cursor",
        "next_cursor",
        "next",
        "nextCursor",
        "continuation",
        "continuation_token"
    ]:
        
        value = response_json.get(key)

        # if the cursor is a non-empty string then the pagination cursor is valid
        # and we can return it. 
        if isinstance(value, str) and value.strip():
            return value

    # try to retrieve the meta data object about the tweets 
    meta = response_json.get("meta")

    # If we couldn't find a pagination cursor in the json we can check the meta data.
    # Checks if the meta data is a dict
    if isinstance(meta, dict):
        for key in ["cursor", "next_cursor", "next"]:
            value = meta.get(key)
            # if we can find a pagination cursor here that's a non-empty string
            # we return that
            if isinstance(value, str) and value.strip():
                return value
            
    # if we can't find a pagination cursor we return None
    return None