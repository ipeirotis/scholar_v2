import logging
from scholarly import scholarly
from datetime import datetime
import pytz
import json
import requests

from data_access import get_firestore_cache, set_firestore_cache



def get_author(author_id):

    cached_author = get_firestore_cache("scholar_raw_author", author_id)
    if cached_author:
        return cached_author
    else:
        return None
    
def get_publication(author_pub_id):

    cached_pub = get_firestore_cache("scholar_raw_pub", author_pub_id)
    if cached_pub:
        return cached_pub
    else:
        return None
        

def get_similar_authors(author_name):
    # Check cache first
    cached_data = get_firestore_cache("queries", author_name)
    if cached_data:
        logging.info(
            f"Cache hit for similar authors of '{author_name}'. Data fetched from Firestore."
        )
        return cached_data

    authors = []
    try:
        search_query = scholarly.search_author(author_name)
        for _ in range(10):  # Limit to 10 authors for simplicity
            try:
                author = next(search_query)
                if author:
                    authors.append(author)
            except StopIteration:
                break
    except Exception as e:
        logging.error(f"Error fetching similar authors for '{author_name}': {e}")
        return []

    # Process authors
    clean_authors = [
        {
            "name": author.get("name", ""),
            "affiliation": author.get("affiliation", ""),
            "email": author.get("email", ""),
            "citedby": author.get("citedby", 0),
            "scholar_id": author.get("scholar_id", ""),
        }
        for author in authors
    ]

    # Cache the results
    set_firestore_cache("queries", author_name, clean_authors)

    return clean_authors
