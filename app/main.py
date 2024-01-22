from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
)


import os
import json
import logging

import pandas as pd
import matplotlib
import numpy as np
from matplotlib.figure import Figure

from sklearn.metrics import auc

from scholar import get_scholar_data, get_similar_authors
from data_analysis import get_author_statistics_by_id

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "secret-key"


def generate_plot(dataframe, author_name):
    plot_paths = []
    pip_auc_score = 0
    try:
        cleaned_name = "".join([c if c.isalnum() else "_" for c in author_name])
        fig = Figure(figsize=(20, 10), dpi=100)
        ax1, ax2 = fig.subplots(1, 2)  # Adjusted for better resolution

        matplotlib.rcParams.update({"font.size": 16})

        marker_size = 40

        # First subplot (Rank vs Percentile Score)
        scatter1 = ax1.scatter(
            dataframe["paper_rank"],
            dataframe["percentile_score"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar1 = fig.colorbar(scatter1, ax=ax1)
        colorbar1.set_label("Years since Publication")
        ax1.set_title(f"Paper Percentile Scores for {author_name}")
        ax1.set_xlabel("Paper Rank")
        ax1.set_ylabel("Paper Percentile Score")
        ax1.grid(True)

        # Second subplot (Productivity Percentiles)
        scatter2 = ax2.scatter(
            dataframe["num_papers_percentile"],
            dataframe["percentile_score"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar2 = fig.colorbar(scatter2, ax=ax2)
        colorbar2.set_label("Years since Publication")
        ax2.set_title(
            f"Paper Percentile Scores vs #Papers Percentile for {author_name}"
        )
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
        auc_data = dataframe.filter(
            ["num_papers_percentile", "percentile_score"]
        ).drop_duplicates(subset="num_papers_percentile", keep="first")
        pip_auc_score = np.trapz(
            auc_data["percentile_score"], auc_data["num_papers_percentile"]
        ) / (100 * 100)
        # print(f"AUC score: {pip_auc_score:.4f}")

    except Exception as e:
        logging.error(f"Error in generate_plot for {author_name}: {e}")
        raise

    return plot_paths, round(pip_auc_score, 4)


def perform_search_by_id(scholar_id):
    author, publications, total_publications = get_author_statistics_by_id(scholar_id)
    has_results = not publications.empty
    pip_auc_score = 0

    try:
        plot_paths, pip_auc_score = (
            generate_plot(publications, author["name"]) if has_results else ([], 0)
        )
    except Exception as e:
        logging.error(f"Error generating plot for {scholar_id}: {e}")
        flash(f"An error occurred while generating the plot for {scholar_id}.", "error")
        plot_paths, pip_auc_score = [], 0

    search_data = {
        "author": author,
        "publications": publications,
        "has_results": has_results,
        "plot_paths": plot_paths,
        "total_publications": total_publications,
        "pip_auc_score": pip_auc_score,
    }

    return search_data


@app.route("/")
def index():
    return render_template("index.html")


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

    if search_data["has_results"]:
        author = search_data
    else:
        flash("Google Scholar ID has no data.")
        return redirect(url_for("index"))

    return render_template("results.html", author=author)


@app.route("/download/<author_id>")
def download_results(author_id):
    author, publications, _ = get_author_statistics_by_id(author_id)

    # Check if there is data to download
    if publications.empty:
        flash("No publications found to download.")
        return redirect(url_for("index"))

    downloads_dir = os.path.join(app.root_path, "downloads")
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)  # Create the downloads directory if it doesn't exist

    file_path = os.path.join(downloads_dir, f"{author_id}_results.csv")

    publications.to_csv(file_path, index=False)

    return send_file(
        file_path, as_attachment=True, download_name=f"{author_id}_results.csv"
    )


@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
