'''
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
import os
from datetime import datetime
import logging
from scholarly_service import get_scholar_data, get_similar_authors
from analytics import calculate_paper_percentiles

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "secret-key"
logging.basicConfig(level=logging.INFO)

@app.route("/")
def index():
    author_count = request.args.get("author_count", default=1, type=int)
    return render_template("index.html", author_count=author_count)

@app.route("/get_similar_authors")
def get_similar_authors_route():
    author_name = request.args.get("author_name")
    if not author_name:
        return jsonify([])

    authors = get_similar_authors(author_name)
    clean_authors = [{
        "name": author.get("name", ""),
        "affiliation": author.get("affiliation", ""),
        "email": author.get("email", ""),
        "citedby": author.get("citedby", 0),
        "scholar_id": author.get("scholar_id", "")
    } for author in authors]

    return jsonify(clean_authors)

@app.route("/results", methods=["GET"])
def results():
    author_id = request.args.get("author_id", "")
    if not author_id:
        flash("Google Scholar ID is required.")
        return redirect(url_for("index"))

    author_data = get_scholar_data(author_id)
    if author_data and 'publications' in author_data:
        author_data['publications'] = calculate_paper_percentiles(author_data['publications'])

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return render_template("results.html", author=author_data, time_stamp=timestamp)

@app.route('/download/<author_id>')
def download_results(author_id):
    author_data = get_scholar_data(author_id)
    if not author_data or 'publications' not in author_data or author_data['publications'].empty:
        flash("No results found to download.")
        return redirect(url_for("index"))

    downloads_dir = os.path.join(app.root_path, 'downloads')
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)

    file_path = os.path.join(downloads_dir, f"{author_id}_results.csv")
    author_data['publications'].to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True, download_name=f"{author_id}_results.csv")

@app.route("/error")
def error():
    return render_template("error.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)



'''


from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from util import (
    get_scholar_data,
    generate_plot,
    get_author_statistics_by_id,
)


import os
from flask import jsonify
from datetime import datetime
import json
import logging
import time
from scholarly import scholarly



logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "secret-key"


def perform_search_by_id(scholar_id):
    author, query, total_publications = get_author_statistics_by_id(scholar_id)
    has_results = not query.empty
    pip_auc_score = 0
    
    try:
        plot_paths, pip_auc_score = generate_plot(query, author["name"]) if has_results else ([], 0)
    except Exception as e:
        logging.error(f"Error generating plot for {scholar_id}: {e}")
        flash(f"An error occurred while generating the plot for {scholar_id}.", "error")
        plot_paths, pip_auc_score = [], 0

    search_data = {
        "author": author,
        "results": query,
        "has_results": has_results,
        "plot_paths": plot_paths,
        "total_publications": total_publications,
        "pip_auc_score": pip_auc_score
    }

    return search_data



@app.route("/")
def index():
    author_count = request.args.get("author_count", default=1, type=int)
    return render_template("index.html", author_count=author_count)


@app.route("/get_similar_authors")
def get_similar_authors():
    author_name = request.args.get("author_name")
    authors = []

    # Primary search attempt
    primary_search = scholarly.search_author(author_name)
    for _ in range(10):
        try:
            author = next(primary_search)
            if author:
                authors.append(author)
        except StopIteration:
            break  # Break the loop if there are no more authors

    # Process and return the authors
    clean_authors = [{
        "name": author.get("name", ""),
        "affiliation": author.get("affiliation", ""),
        "email": author.get("email", ""),
        "citedby": author.get("citedby", 0),
        "scholar_id": author.get("scholar_id", "")
    } for author in authors]

    return jsonify(clean_authors)

@app.route("/results", methods=["GET"])
def results():
    author_id = request.args.get("author_id", "")

    if not author_id:
        flash("Google Scholar ID is required.")
        return redirect(url_for("index"))

    search_data = perform_search_by_id(author_id)

    if search_data['has_results']:
        author = search_data
    else:
        flash("Google Scholar ID has no data.")
        return redirect(url_for("index"))

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return render_template("results.html", author=author, time_stamp=timestamp)



@app.route('/download/<author_id>')
def download_results(author_id):
    author, query, _ = get_author_statistics_by_id(author_id)

    # Check if there is data to download
    if query.empty:
        flash("No results found to download.")
        return redirect(url_for("index"))

    downloads_dir = os.path.join(app.root_path, 'downloads')
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)  # Create the downloads directory if it doesn't exist

    file_path = os.path.join(downloads_dir, f"{author_id}_results.csv")

    query.to_csv(file_path, index=False)

    return send_file(
        file_path, as_attachment=True, download_name=f"{author_id}_results.csv"
    )



@app.route("/error")
def error():
    return render_template("error.html")

from scholarly_service import get_scholar_data
from analytics import calculate_paper_percentiles

@app.route("/results2", methods=["GET"])
def results():
    author_id = request.args.get("author_id", "")
    if not author_id:
        flash("Google Scholar ID is required.")
        return redirect(url_for("index"))

    author_data = get_scholar_data(author_id)
    if author_data and 'publications' in author_data:
        author_data['publications'] = calculate_paper_percentiles(author_data['publications'])

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return render_template("results.html", author=author_data, time_stamp=timestamp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
