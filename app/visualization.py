import matplotlib
from matplotlib.figure import Figure
import logging
import numpy as np

import base64
from io import BytesIO


def generate_percentile_rank_plot(dataframe, author_name):
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
