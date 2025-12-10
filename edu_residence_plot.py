import pandas as pd
import plotly.express as px

# Load dataset
df = pd.read_csv("violence_data.csv")

# Function to create the chart
def plot_edu_residence(gender="All"):
    data = df.copy()

    # Filter gender
    if gender != "All":
        data = data[data["gender"] == gender]

    # Keep only education & residence rows
    data = data[data["demo_question"].isin(["education", "residence"])]

    # Pivot: education as rows, rural/urban as columns
    pivot = data.pivot_table(
        index="demo_response",
        columns="residence",
        values="value",
        aggfunc="mean"
    ).reset_index()

    # Sort x-axis
    edu_order = ["No education", "Primary", "Secondary", "Higher"]
    pivot = pivot[pivot["demo_response"].isin(edu_order)]
    pivot["demo_response"] = pd.Categorical(pivot["demo_response"], categories=edu_order, ordered=True)
    pivot = pivot.sort_values("demo_response")

    # Plot
    fig = px.line(
        pivot,
        x="demo_response",
        y=["Rural", "Urban"],
        markers=True,
        labels={"value": "Violence Acceptance (%)", "demo_response": "Education Level"},
        title="Violence Acceptance Rate by Education × Residence"
    )

    fig.update_layout(
        yaxis=dict(range=[0, 80]),
        legend_title="Residence Type"
    )

    return fig

# Run standalone
if __name__ == "__main__":
    fig = plot_edu_residence("All")
    fig.show()
