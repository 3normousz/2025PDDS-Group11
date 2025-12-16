import pandas as pd
import plotly.graph_objects as go

# Load data
df = pd.read_csv(
    r"C:\Users\ThinkPad X1 Carbon\Downloads\NTHU studying\Semester 3\PDDS\Clean_Data_ver2.csv"
)

# Column names (EXACT)
edu_col = "%higher_edu_attained"
value_col = "value"

# Make value numeric
df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

# ---- Create education groups ----
edu_num = pd.to_numeric(df[edu_col], errors="coerce")

if edu_num.notna().any():
    # Numeric case
    df["edu_group"] = pd.cut(
        edu_num,
        bins=[-1, 10, 25, 1e9],
        labels=["Low (<10%)", "Medium (10–25%)", "High (>25%)"]
    )
else:
    # Categorical case
    mapping = {
        "<10%": "Low (<10%)",
        "10-25%": "Medium (10–25%)",
        ">25%": "High (>25%)",
        "10–25%": "Medium (10–25%)"
    }
    df["edu_group"] = df[edu_col].astype(str).str.strip().map(mapping)

# Drop missing
df = df.dropna(subset=["edu_group", value_col])

# ---- Calculate averages ----
group_avg = (
    df.groupby("edu_group", observed=True)[value_col]
      .mean()
      .round(0)
      .astype(int)
      .reindex(["Low (<10%)", "Medium (10–25%)", "High (>25%)"])
      .reset_index()
)

# ---- COLOR RULE: LOWEST = PURPLE ----
min_val = group_avg[value_col].min()
colors = ["#B9A6FF" if v == min_val else "#D5D3D2" for v in group_avg[value_col]]

# ---- Plot (Plotly) ----
fig = go.Figure(go.Bar(
    x=group_avg["edu_group"],
    y=group_avg[value_col],
    marker_color=colors,
    text=group_avg[value_col],
    textposition="inside",
    textfont=dict(size=22, color="black"),
    width=0.55,
    hovertemplate="%{x}<br>%{y}%<extra></extra>"
))

fig.update_layout(
    title=dict(
        text="DOMESTIC VIOLENCE ACCEPTANCE VS.<br>HIGHER EDUCATION ATTAINMENT",
        x=0.5,
        xanchor="center",
        font=dict(size=34, family="Arial Black")
    ),
    xaxis_title="Population with Higher Education (%)",
    yaxis_title="Avg Violence Acceptance Rate",
    bargap=0.15,
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    height=420,
    margin=dict(t=120, l=80, r=40, b=80)
)

fig.update_yaxes(showgrid=False, zeroline=False)
fig.update_xaxes(showgrid=False)

fig.show()
