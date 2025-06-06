import matplotlib.pyplot as plt

# MathonGo Brand Colors
PRIMARY_BLUE = "#0033A0"
ACCENT_ORANGE = "#FF7F00"
DARK_GRAY = "#333333"
LIGHT_GRAY = "#F5F5F5"

def plot_accuracy_over_time(df_all):
    """
    df_all: DataFrame with columns ['timestamp', 'accuracy', ...]
    Returns a Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.plot(
        df_all["timestamp"],
        df_all["accuracy"],
        color=PRIMARY_BLUE,
        linewidth=2,
        marker="o",
        markerfacecolor=ACCENT_ORANGE,
        markeredgecolor=PRIMARY_BLUE,
        markersize=6,
    )
    ax.set_facecolor(LIGHT_GRAY)
    ax.grid(color=DARK_GRAY, linestyle="--", linewidth=0.5, alpha=0.4)
    
    ax.set_xlabel("Timestamp", color=DARK_GRAY, fontsize=10)
    ax.set_ylabel("Accuracy (%)", color=DARK_GRAY, fontsize=10)
    ax.tick_params(colors=DARK_GRAY)
    ax.set_title("Accuracy vs. Time", color=PRIMARY_BLUE, fontsize=12, pad=8)
    
    # Rotate x-axis labels if datetime
    fig.autofmt_xdate(rotation=25)
    
    return fig

def plot_chapter_breakdown(chapter_summary_df):
    """
    chapter_summary_df: DataFrame with columns ['chapter', 'accuracy', 'avg_time_spent', 'num_questions']
    Returns a Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Sort chapters by accuracy ascending so the lowest appear at bottom
    df_sorted = chapter_summary_df.sort_values("accuracy", ascending=True)
    
    ax.barh(
        df_sorted["chapter"],
        df_sorted["accuracy"],
        color=PRIMARY_BLUE,
        edgecolor=DARK_GRAY,
        height=0.6
    )
    ax.set_facecolor(LIGHT_GRAY)
    ax.grid(axis="x", color=DARK_GRAY, linestyle="--", linewidth=0.5, alpha=0.4)
    
    ax.set_xlabel("Average Accuracy (%)", color=DARK_GRAY, fontsize=10)
    ax.set_ylabel("Chapter", color=DARK_GRAY, fontsize=10)
    ax.tick_params(colors=DARK_GRAY)
    ax.set_title("Chapter‐wise Performance", color=PRIMARY_BLUE, fontsize=12, pad=8)
    
    return fig

    # app/charts.py

import matplotlib.pyplot as plt

# (existing color constants: PRIMARY_BLUE, ACCENT_ORANGE, DARK_GRAY, LIGHT_GRAY)

def plot_subject_breakdown(subject_summary_df):
    """
    subject_summary_df: DataFrame with columns ['subject_id', 'accuracy', ...]
    Returns a Matplotlib figure of subject vs. accuracy.
    """
    if subject_summary_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No subject data", ha="center", va="center")
        return fig

    # Sort by accuracy
    df_sorted = subject_summary_df.sort_values("accuracy", ascending=True)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(
        df_sorted["subject_id"],
        df_sorted["accuracy"],
        color=PRIMARY_BLUE,
        edgecolor=DARK_GRAY,
        height=0.6
    )
    ax.set_facecolor(LIGHT_GRAY)
    ax.grid(axis="x", color=DARK_GRAY, linestyle="--", linewidth=0.5, alpha=0.4)
    ax.set_xlabel("Accuracy (%)", color=DARK_GRAY, fontsize=10)
    ax.set_ylabel("Subject ID", color=DARK_GRAY, fontsize=10)
    ax.tick_params(colors=DARK_GRAY)
    ax.set_title("Subject‐wise Performance", color=PRIMARY_BLUE, fontsize=12, pad=8)

    return fig
