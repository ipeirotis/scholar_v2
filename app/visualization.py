import matplotlib
from matplotlib.figure import Figure
import logging
import numpy as np
import os
import datetime


def generate_plot(dataframe, author_name):
    plot_paths = []

    current_year = datetime.datetime.now().year

    dataframe["age"] = current_year - dataframe["pub_year"] + 1
    dataframe["num_citations_percentile"] = 100 * dataframe["num_citations_percentile"]
    dataframe["num_papers_percentile"] = 100 * dataframe["num_papers_percentile"]

    try:
        cleaned_name = "".join([c if c.isalnum() else "_" for c in author_name])
        fig = Figure(figsize=(20, 10), dpi=100)
        ax1, ax2 = fig.subplots(1, 2)  # Adjusted for better resolution

        matplotlib.rcParams.update({"font.size": 16})

        marker_size = 40

        # First subplot (Rank vs Percentile Score)
        scatter1 = ax1.scatter(
            dataframe["publication_rank"],
            dataframe["num_citations_percentile"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar1 = fig.colorbar(scatter1, ax=ax1)
        colorbar1.set_label("Years since Publication")
        ax1.set_title(f"Paper Percentile Scores for {author_name}")
        ax1.set_yticks(np.arange(0, 110, step=10))  # Adjust step as needed
        ax1.grid(True, color="lightgray", linestyle="--")
        ax1.set_xlabel("Paper Rank")
        ax1.set_ylabel("Paper Percentile Score")

        # Second subplot (Productivity Percentiles)
        scatter2 = ax2.scatter(
            dataframe["num_papers_percentile"],
            dataframe["num_citations_percentile"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar2 = fig.colorbar(scatter2, ax=ax2)
        colorbar2.set_label("Years since Publication")
        ax2.set_title(f"Paper Percentile Scores vs #Papers Percentile for {author_name}")
        ax2.set_xlabel("Number of Papers Published Percentile")
        ax2.set_ylabel("Paper Percentile Score")
        ax2.grid(True, color="lightgray", linestyle="--")
        ax2.set_xticks(np.arange(0, 110, step=10))  # Adjust step as needed
        ax2.set_yticks(np.arange(0, 110, step=10))  # Adjust step as needed

        fig.tight_layout()
        combined_plot_path = os.path.join("static", f"{cleaned_name}_combined_plot.png")
        fig.savefig(combined_plot_path)
        plot_paths.append(combined_plot_path)

    except Exception as e:
        logging.error(f"Error in generate_plot for {author_name}: {e}")
        raise

    return plot_paths


def generate_percentile_rank_plot(dataframe, author_name):

    cleaned_name = "".join([c if c.isalnum() else "_" for c in author_name])
    current_year = datetime.datetime.now().year

    dataframe["age"] = current_year - dataframe["pub_year"] + 1
    dataframe["num_citations_percentile"] = 100 * dataframe["num_citations_percentile"]

    try:
        
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.subplots(1, 1)  # Adjusted for better resolution

        matplotlib.rcParams.update({"font.size": 16})

        marker_size = 40

        # First subplot (Rank vs Percentile Score)
        scatter = ax.scatter(
            dataframe["publication_rank"],
            dataframe["num_citations_percentile"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label("Years since Publication")
        ax.set_title(f"Paper Percentile Scores for {author_name}")
        ax.set_yticks(np.arange(0, 110, step=10))  # Adjust step as needed
        ax.grid(True, color="lightgray", linestyle="--")
        ax.set_xlabel("Paper Rank")
        ax.set_ylabel("Paper Percentile Score")

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        data = base64.b64encode(buf.getbuffer()).decode("ascii")

    except Exception as e:
        logging.error(f"Error in generate_plot for {author_name}: {e}")
        raise

    return f"data:image/png;base64,{data}"



def generate_pip_plot(dataframe, author_name):

    current_year = datetime.datetime.now().year
    cleaned_name = "".join([c if c.isalnum() else "_" for c in author_name])
        

    dataframe["age"] = current_year - dataframe["pub_year"] + 1
    dataframe["num_citations_percentile"] = 100 * dataframe["num_citations_percentile"]
    dataframe["num_papers_percentile"] = 100 * dataframe["num_papers_percentile"]

    try:
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.subplots(1, 1)

        matplotlib.rcParams.update({"font.size": 16})

        marker_size = 40


        # Second subplot (Productivity Percentiles)
        scatter = ax.scatter(
            dataframe["num_papers_percentile"],
            dataframe["num_citations_percentile"],
            c=dataframe["age"],
            cmap="Blues_r",
            s=marker_size,
        )
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label("Years since Publication")
        ax.set_title(f"Paper Percentile Scores vs #Papers Percentile for {author_name}")
        ax.set_xlabel("Number of Papers Published Percentile")
        ax.set_ylabel("Paper Percentile Score")
        ax.grid(True, color="lightgray", linestyle="--")
        ax.set_xticks(np.arange(0, 110, step=10))  # Adjust step as needed
        ax.set_yticks(np.arange(0, 110, step=10))  # Adjust step as needed

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        
    except Exception as e:
        logging.error(f"Error in generate_plot for {author_name}: {e}")
        raise

    return f"data:image/png;base64,{data}"


