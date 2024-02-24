import functions_framework
import json
import logging
from flask import make_response, jsonify
from scholarly import scholarly

from shared.config import Config
from shared.utils import convert_integers_to_strings
from shared.services.firestore_service import FirestoreService
from shared.services.task_queue_service import TaskQueueService

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Instantiate services
firestore_service = FirestoreService()
task_queue_service = TaskQueueService()


@functions_framework.http
def search_author_id(request):
    """Responds to HTTP requests with author information from Google Scholar.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        flask.Response: HTTP response object.
    """
    scholar_id = request.args.get('scholar_id') or (request.get_json(silent=True) or {}).get('scholar_id')

    if not scholar_id:
        return jsonify({"error": "Missing author id"}), 400

    author_info = process_author(scholar_id)
    if author_info is None:
        return jsonify({"error": "Failed to fetch or process author data"}), 500

    return jsonify(author_info), 200


def process_author(scholar_id):
    """Fetches and processes an author's information and publications.
    Args:
        scholar_id (str): Google Scholar ID of the author.
    Returns:
        dict: Serialized author information, or None upon failure.
    """
    author = fetch_author(scholar_id)
    if author is None:
        return None

    enqueue_publications(author.get('publications', []))
    serialized_author = serialize_author(author)
    if not serialized_author:
        return None

    if not firestore_service.set_firestore_cache("scholar_raw_author", scholar_id, serialized_author):
        logging.error(f"Failed to store author {scholar_id} in Firestore.")
        return None

    return serialized_author


def fetch_author(scholar_id):
    """Fetches detailed author data from Google Scholar.
    Args:
        scholar_id (str): The unique identifier for the author.
    Returns:
        dict: Author data, or None if an error occurs.
    """
    try:
        logging.info(f"Fetching author entry for {scholar_id}")
        return scholarly.fill(scholarly.search_author_id(scholar_id))
    except Exception as e:
        logging.error(f"Error fetching author data for {scholar_id}: {e}")
        return None


def enqueue_publications(publications):
    """Enqueues tasks for processing each publication.
    Args:
        publications (list): A list of publication data dictionaries.
    """
    for pub in publications:
        if not task_queue_service.enqueue_publication_task(pub):
            logging.error(f"Failed to enqueue publication task for {pub.get('author_pub_id')}")


def serialize_author(author):
    """Serializes author data for storage, handling large data sizes.
    Args:
        author (dict): The author data to serialize.
    Returns:
        dict: The serialized author data.
    """
    try:
        author['publications'] = [
            {
                "author_pub_id": pub.get("author_pub_id"),
                "num_citations": pub.get("num_citations", 0),
                "filled": False,
                "bib": {key: pub['bib'][key] for key in ['pub_year'] if key in pub.get('bib', {})}
            } for pub in author.get('publications', []) if pub.get("author_pub_id")
        ]
        serialized = convert_integers_to_strings(json.loads(json.dumps(author)))  # Simplified serialization
        return serialized
    except Exception as e:
        logging.error(f"Error serializing author data: {e}")
        return None




