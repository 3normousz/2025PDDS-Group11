import os
from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__, static_folder='static')

# Fonts path, you can just directly refer to this in your Plotly
glacial_indifference = os.path.join(os.getcwd(), "assets/fonts/", "GlacialIndifference-Regular.otf")

# Dataset path
dataset_path = os.path.join(os.getcwd(), "data/makeovermonday-2020w10/", "violence_data.csv")

@app.route("/")
def index():
    try:
        df = pd.read_csv(dataset_path)

        # subset = df[(df['Gender'] == 'F') & (df['Question'] == '... for at least one specific reason')]
        # subset = df[(df['Gender'] == 'F')]
        mask = df['Question'].astype(str).str.strip() == '... for at least one specific reason'
        subset = df[mask].copy()

        # Ensure 'Value' is numeric and drop missing values
        values = pd.to_numeric(subset['Value'], errors='coerce').dropna()
        percentage = round(values.mean(), 1) if not values.empty else 0

        ratio = int(round(100 / percentage)) if percentage > 0 else 0
        
        text = f"1 AMONG {ratio} PEOPLE THINK THAT DOMESTIC VIOLENCE IS ACCEPTABLE"

    except Exception as e:
        print(f"Error calculating hook data: {e}")
        percentage = 0
        ratio = 0
        text = "Data Unavailable"

    return render_template("index.html", percentage=percentage, text=text, ratio=ratio)

@app.route("/heat-map")
def heat_map():
    return render_template("heat_map.html")

@app.route("/reason-gender")
def reason_gender_page():
    return render_template("reason_gender.html")

@app.route("/api/world-heatmap")
def world_heatmap_api():
    try:
        df = pd.read_csv(dataset_path)
        
        country_data = df[df['Value'].notna()].groupby('Country')['Value'].mean().reset_index()
        country_data.columns = ['Country', 'Average_Violence_Score']
        
        data_dict = {}
        for _, row in country_data.iterrows():
            data_dict[row['Country']] = row['Average_Violence_Score']
        
        return jsonify(data_dict), 200
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in world_heatmap_api: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500


@app.route("/api/reason-gender")
def reason_gender_api():
    try:
        df = pd.read_csv(dataset_path)

        df = df[df['Value'].notna()].copy()

        df['Reason'] = df['Question'].astype(str).str.strip()

        grouped = (
            df.groupby(['Reason', 'Gender'])['Value']
            .mean()
            .reset_index()
        )

        # Pivot into { reason: { M: value, F: value } }
        result = {}
        for _, row in grouped.iterrows():
            reason = row['Reason']
            gender = row['Gender']
            value = float(row['Value'])
            if reason not in result:
                result[reason] = {"M": None, "F": None}
            result[reason][gender] = value

        return jsonify(result), 200

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in reason_gender_api: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route("/api/locations")
def locations_api():
    try:
        df = pd.read_csv(dataset_path)
        countries = df['Country'].unique().tolist()
        
        region_map = {
            "Africa": [
                "Angola", "Benin", "Burkina Faso", "Burundi", "Cameroon", "Chad", "Comoros", 
                "Congo", "Congo Democratic Republic", "Cote d'Ivoire", "Egypt", "Eritrea", 
                "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Kenya", 
                "Lesotho", "Liberia", "Madagascar", "Malawi", "Mali", "Morocco", "Mozambique", 
                "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "Senegal", 
                "Sierra Leone", "South Africa", "Tanzania", "Togo", "Uganda", "Zambia", "Zimbabwe"
            ],
            "Asia": [
                "Afghanistan", "Armenia", "Azerbaijan", "Bangladesh", "Cambodia", "India", 
                "Indonesia", "Jordan", "Kyrgyz Republic", "Maldives", "Myanmar", "Nepal", 
                "Pakistan", "Philippines", "Tajikistan", "Timor-Leste", "Turkey", "Turkmenistan", "Yemen"
            ],
            "Europe": [
                "Albania", "Moldova", "Ukraine"
            ],
            "North America": [
                "Dominican Republic", "Guatemala", "Haiti", "Honduras", "Nicaragua"
            ],
            "South America": [
                "Bolivia", "Colombia", "Guyana", "Peru"
            ]
        }
        
        # Identify countries not in any region and add them to "Other"
        mapped_countries = set()
        for countries_list in region_map.values():
            mapped_countries.update(countries_list)
            
        others = [c for c in countries if c not in mapped_countries]
        if others:
            region_map["Other"] = others

        return jsonify(region_map), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/impact-data")
def impact_data_api():
    try:
        df = pd.read_csv(dataset_path)
        
        # Compute impact and sort descending
        def compute_impact_sorted(selected_country):
            if selected_country != "Worldwide":
                sub = df[df["Country"] == selected_country]
            else:
                sub = df.copy()

            if sub.empty:
                return {"demo_question": [], "impact": [], "color": []}

            # Average acceptance for each subgroup
            group_means = (
                sub.groupby(["Demographics Question", "Demographics Response"])["Value"]
                .mean()
                .reset_index()
            )

            # Impact = highest - lowest subgroup acceptance
            impact = (
                group_means.groupby("Demographics Question")["Value"]
                .agg(lambda x: x.max() - x.min())
                .reset_index()
                .rename(columns={"Value": "impact"})
            )

            impact["impact"] = impact["impact"].fillna(0).round(1)

            # Sort descending
            impact = impact.sort_values("impact", ascending=False).reset_index(drop=True)

            # Highlight max factor in purple
            colors = ["#8A2BE2"] + ["#D9D9D9"] * (len(impact) - 1)
            
            return {
                "demo_question": impact["Demographics Question"].tolist(),
                "impact": impact["impact"].tolist(),
                "color": colors
            }

        countries = ["Worldwide"] + sorted(df["Country"].unique())
        impact_by_country = {c: compute_impact_sorted(c) for c in countries}
        
        return jsonify(impact_by_country), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/api/edu-residence")
def edu_residence_api():
    try:
        df = pd.read_csv(dataset_path)
        
        EDU_ORDER = ["No education", "Primary", "Secondary", "Higher"]
        gender_map = {"F": "Female", "M": "Male"}

        # Filter for Education data
        edu = df[df["Demographics Question"] == "Education"].copy()
        
        # Map Gender
        edu["Gender"] = edu["Gender"].map(gender_map)

        # Ensure Value is numeric
        edu["Value"] = pd.to_numeric(edu["Value"], errors='coerce')
        edu = edu.dropna(subset=["Value", "Gender"])

        # Group by Education and Gender (Worldwide average)
        plot_df = (
            edu.groupby(["Demographics Response", "Gender"])["Value"]
            .mean()
            .reset_index()
            .rename(columns={"Demographics Response": "Education"})
        )
        
        # Sort Education
        plot_df["Education"] = pd.Categorical(
            plot_df["Education"],
            categories=EDU_ORDER,
            ordered=True
        )
        plot_df = plot_df.sort_values("Education")

        # Prepare traces
        traces = []
        colors = {"Female": "#9b14be", "Male": "#decdff"}
        
        for gender in ["Female", "Male"]:
            gender_data = plot_df[plot_df["Gender"] == gender]
            if not gender_data.empty:
                traces.append({
                    "x": gender_data["Education"].tolist(),
                    "y": gender_data["Value"].tolist(),
                    "name": gender,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "line": {"color": colors.get(gender, "#000000")},
                    "marker": {"size": 8}
                })

        return jsonify(traces)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)