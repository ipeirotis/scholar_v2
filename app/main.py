
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify


import os
from datetime import datetime
import json
import logging
import time
from scholarly import scholarly


import pandas as pd
import matplotlib
import numpy as np
from scholarly import scholarly
from datetime import datetime, timedelta
from matplotlib.figure import Figure
import os
import logging
from sklearn.metrics import auc
import pytz
from google.cloud import firestore

from data_access import get_firestore_cache, set_firestore_cache
from scholar import get_scholar_data, fetch_from_scholar, extract_author_info, sanitize_author_data, sanitize_publication_data, get_similar_authors


db = firestore.Client()
url = "../data/percentiles.csv"
percentile_df = pd.read_csv(url).set_index("age")
percentile_df.columns = [float(p) for p in percentile_df.columns]


url_author_percentiles = "../data/author_numpapers_percentiles.csv"
author_percentiles = pd.read_csv(url_author_percentiles).set_index(
    "years_since_first_pub"
)



logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "secret-key"


def get_numpaper_percentiles(year):
    # If the exact year is in the index, use that year
    if year in author_percentiles.index:
        s = author_percentiles.loc[year, :]
    else:
        # If the specific year is not in the index, find the closest year
        closest_year = min(author_percentiles.index, key=lambda x: abs(x - year))
        
        valid_range = range(0, 100)
        if not all(value in valid_range for value in author_percentiles.loc[closest_year]):
            years = sorted(author_percentiles.index)
            year_index = years.index(closest_year)
            prev_year = years[max(0, year_index - 1)]
            next_year = years[min(len(years) - 1, year_index + 1)]
            s = (author_percentiles.loc[prev_year, :] + author_percentiles.loc[next_year, :]) / 2
        else:
            s = author_percentiles.loc[closest_year, :]
    
    highest_indices = s.groupby(s).apply(lambda x: x.index[-1])
    sw = pd.Series(index=highest_indices.values, data=highest_indices.index)
    normalized_values = pd.Series(data=sw.index, index=sw.values)
    return normalized_values




def find_closest(series, number):
    if series.empty:
        return np.nan
    differences = np.abs(series.index - number)
    closest_index = differences.argmin()
    return series.iloc[closest_index]
    

def score_papers(row):
    age, citations = row["age"], row["citations"]
    
    if age not in percentile_df.index:
        closest_year = percentile_df.index[np.abs(percentile_df.index - age).argmin()]
        percentiles = percentile_df.loc[closest_year]
    else:
        percentiles = percentile_df.loc[age]

    if citations <= percentiles.min():
        return 0.0
    elif citations >= percentiles.max():
        return 100.0
    else:
        below = percentiles[percentiles <= citations].idxmax()
        above = percentiles[percentiles >= citations].idxmin()
        if above == below:
            return above
        else:
            lower_bound = percentiles[below]
            upper_bound = percentiles[above]
            weight = (citations - lower_bound) / (upper_bound - lower_bound)
            return below + weight * (above - below)



def get_author_statistics_by_id(scholar_id):

    author_info, publications, total_publications, error = get_scholar_data(scholar_id)

    if error:
        logging.error(f"Error fetching data for author with ID {scholar_id}: {error}")
        return None, pd.DataFrame(), 0

    if not publications:
        logging.error(f"No valid publication data found for author with ID {scholar_id}.")
        return None, pd.DataFrame(), 0

    publications_df = pd.DataFrame(publications)

    publications_df["percentile_score"] = publications_df.apply(score_papers, axis=1).round(2)
    publications_df["paper_rank"] = publications_df["percentile_score"].rank(ascending=False, method='first').astype(int)
    publications_df = publications_df.sort_values("percentile_score", ascending=False)
    
    year = publications_df['age'].max()
    num_papers_percentile = get_numpaper_percentiles(year)
    if num_papers_percentile.empty:
        logging.error("Empty num_papers_percentile series.")
        return None, pd.DataFrame(), 0

    publications_df['num_papers_percentile'] = publications_df['paper_rank'].apply(lambda x: find_closest(num_papers_percentile, x))
    publications_df['num_papers_percentile'] = publications_df['num_papers_percentile'].astype(float)
    publications_df = publications_df.sort_values('percentile_score', ascending=False)

    return author_info, publications_df, total_publications



def generate_plot(dataframe, author_name):
    plot_paths = []
    pip_auc_score = 0
    try:
        cleaned_name = "".join([c if c.isalnum() else "_" for c in author_name])
        fig = Figure(figsize=(20, 10), dpi=100)
        ax1, ax2 = fig.subplots(1, 2)  # Adjusted for better resolution
        
        matplotlib.rcParams.update({'font.size': 16})
       
        marker_size = 40

        # First subplot (Rank vs Percentile Score)
        scatter1 = ax1.scatter(
            dataframe["paper_rank"],
            dataframe["percentile_score"],
            c=dataframe['age'],
            cmap="Blues_r",
            s=marker_size 
        )
        colorbar1 = fig.colorbar(scatter1, ax=ax1) 
        colorbar1.set_label('Years since Publication')
        ax1.set_title(f"Paper Percentile Scores for {author_name}")
        ax1.set_xlabel("Paper Rank")
        ax1.set_ylabel("Paper Percentile Score")
        ax1.grid(True) 

        # Second subplot (Productivity Percentiles)
        scatter2 = ax2.scatter(
            dataframe['num_papers_percentile'],
            dataframe['percentile_score'],
            c=dataframe['age'],
            cmap='Blues_r',
            s=marker_size  
        )
        colorbar2 = fig.colorbar(scatter2, ax=ax2) 
        colorbar2.set_label('Years since Publication')
        ax2.set_title(f"Paper Percentile Scores vs #Papers Percentile for {author_name}")
        ax2.set_xlabel("Number of Papers Published Percentile")
        ax2.set_ylabel("Paper Percentile Score")
        ax2.grid(True) 
        ax2.set_xlim(0, 100)
        ax2.set_ylim(0, 100)

        fig.tight_layout()
        combined_plot_path = os.path.join("static", f"{cleaned_name}_combined_plot.png")
        fig.savefig(combined_plot_path)
        plot_paths.append(combined_plot_path)

        # Calculate AUC score
        auc_data = dataframe.filter(['num_papers_percentile', 'percentile_score']).drop_duplicates(subset='num_papers_percentile', keep='first')
        pip_auc_score = np.trapz(auc_data['percentile_score'], auc_data['num_papers_percentile']) / (100 * 100)
        # print(f"AUC score: {pip_auc_score:.4f}")

    except Exception as e:
        logging.error(f"Error in generate_plot for {author_name}: {e}")
        raise

    return plot_paths, round(pip_auc_score,4)




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
def get_similar_authors_route():
    author_name = request.args.get("author_name")
    authors = get_similar_authors(author_name)
    return jsonify(authors)



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

    return render_template("results.html", author=author)



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



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
