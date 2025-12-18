import os
from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fractions import Fraction

app = Flask(__name__, static_folder='static')

# Fonts path, you can just directly refer to this in your Plotly
glacial_indifference = os.path.join(os.getcwd(), "assets/fonts/", "GlacialIndifference-Regular.otf")

# Dataset path
dataset_path = os.path.join(os.getcwd(), "data/makeovermonday-2020w10/", "violence_data.csv")

REGION_MAP = {
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

@app.route("/")
def index():
    try:
        df = pd.read_csv(dataset_path)

        # Filter for Women and the specific question
        mask_question = df['question'].astype(str).str.strip() == '... for at least one specific reason'
        mask_gender = df['gender'] == 'F'
        subset = df[mask_question & mask_gender].copy()

        # Ensure 'value' is numeric and drop missing values
        values = pd.to_numeric(subset['value'], errors='coerce').dropna()
        percentage = values.mean() if not values.empty else 0

        # Calculate fraction
        if percentage > 0:
            frac = Fraction(percentage/100).limit_denominator(10)
            ratio_text = f"{frac.numerator}/{frac.denominator}"
        else:
            ratio_text = "0/0"
        
        # text variable is kept just in case, but we will use ratio_text in the template
        text = f"{ratio_text} WOMEN THINK THAT VIOLENCE AGAINST THEM COULD BE ACCEPTED"

    except Exception as e:
        print(f"Error calculating hook data: {e}")
        percentage = 0
        ratio_text = "N/A"
        text = "Data Unavailable"

    return render_template("index.html", percentage=percentage, text=text, ratio_text=ratio_text)

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
        
        # Average violence score per country
        country_scores = df[df['value'].notna()].groupby('country')['value'].mean()
        
        # Education level per country 
        country_edu = df.groupby('country')['%higher_edu_attained'].first()
        
        data_dict = {}
        for country in country_scores.index:
            data_dict[country] = {
                "score": country_scores[country],
                "edu": country_edu.get(country, "N/A")
            }
        
        return jsonify(data_dict), 200
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in world_heatmap_api: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500


@app.route("/api/regions")
def regions_api():
    try:
        return jsonify(list(REGION_MAP.keys())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/countries")
def countries_api():
    try:
        region = request.args.get('region')
        
        if region and region in REGION_MAP:
            return jsonify(REGION_MAP[region]), 200
        
        # If no region or invalid region, return all countries
        # We can get all countries from the CSV or just flatten the map
        df = pd.read_csv(dataset_path)
        countries = sorted(df['country'].unique().tolist())
        return jsonify(countries), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reason-gender")
def reason_gender_api():
    try:
        df = pd.read_csv(dataset_path)

        df = df[df['value'].notna()].copy()

        # Filter by Region/Country
        region = request.args.get('region')
        country = request.args.get('country')

        if country and country != "All Countries" and country != "null":
            df = df[df['country'] == country]
        elif region and region != "All Regions" and region != "null":
            if region in REGION_MAP:
                countries_in_region = REGION_MAP[region]
                df = df[df['country'].isin(countries_in_region)]
            elif region == "Other":
                 pass

        df['Reason'] = df['question'].astype(str).str.strip()

        grouped = (
            df.groupby(['Reason', 'gender'])['value']
            .mean()
            .reset_index()
        )

        # Pivot into { reason: { M: value, F: value } }
        result = {}
        for _, row in grouped.iterrows():
            reason = row['Reason']
            gender = row['gender']
            value = float(row['value'])
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
        countries = df['country'].unique().tolist()
        
        # Identify countries not in any region and add them to "Other"
        mapped_countries = set()
        for countries_list in REGION_MAP.values():
            mapped_countries.update(countries_list)
            
        others = [c for c in countries if c not in mapped_countries]
        
        # Create a copy to avoid modifying the global REGION_MAP
        response_map = REGION_MAP.copy()
        if others:
            response_map["Other"] = others

        return jsonify(response_map), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/impact-data")
def impact_data_api():
    try:
        df = pd.read_csv(dataset_path)
        
        # Compute impact and sort descending
        def compute_impact_sorted(selected_country):
            if selected_country != "Worldwide":
                sub = df[df["country"] == selected_country]
            else:
                sub = df.copy()

            if sub.empty:
                return {"demo_question": [], "impact": [], "color": []}

            # Average acceptance for each subgroup
            group_means = (
                sub.groupby(["demo_question", "demo_response"])["value"]
                .mean()
                .reset_index()
            )

            # Impact = highest - lowest subgroup acceptance
            impact = (
                group_means.groupby("demo_question")["value"]
                .agg(lambda x: x.max() - x.min())
                .reset_index()
                .rename(columns={"value": "impact"})
            )

            impact["impact"] = impact["impact"].fillna(0).round(1)

            # Sort descending
            impact = impact.sort_values("impact", ascending=False).reset_index(drop=True)

            # Highlight max factor in purple
            colors = ["#8A2BE2"] + ["#D9D9D9"] * (len(impact) - 1)
            
            return {
                "demo_question": impact["demo_question"].tolist(),
                "impact": impact["impact"].tolist(),
                "color": colors
            }

        countries = ["Worldwide"] + sorted(df["country"].unique())
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

        # Filter by Region/Country
        region = request.args.get('region')
        country = request.args.get('country')

        if country and country != "All Countries" and country != "null":
            df = df[df['country'] == country]
        elif region and region != "All Regions" and region != "null":
            if region in REGION_MAP:
                countries_in_region = REGION_MAP[region]
                df = df[df['country'].isin(countries_in_region)]

        # Filter for Education data
        edu = df[df['demo_question'] == "Education"].copy()
        
        # Map Gender
        edu['gender'] = edu['gender'].map(gender_map)

        # Ensure Value is numeric
        edu['value'] = pd.to_numeric(edu['value'], errors='coerce')
        edu = edu.dropna(subset=['value', 'gender'])

        # Group by Education and Gender
        plot_df = (
            edu.groupby(['demo_response', 'gender'])['value']
            .mean()
            .reset_index()
            .rename(columns={'demo_response': "Education"})
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
        # Male (grey #d1d0d0), Female (purple #bb99ff)
        colors = {"Female": "#bb99ff", "Male": "#d1d0d0"}
        
        for gender in ["Female", "Male"]:
            gender_data = plot_df[plot_df['gender'] == gender]
            if not gender_data.empty:
                traces.append({
                    "x": gender_data["Education"].tolist(),
                    "y": gender_data['value'].tolist(),
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

@app.route("/api/education-impact")
def education_impact_api():
    try:
        df = pd.read_csv(dataset_path)
        
        # Filter by Region/Country
        region = request.args.get('region')
        country = request.args.get('country')

        # Handle column names (case-insensitive)
        cols = {c.lower(): c for c in df.columns}
        country_col = cols.get("country", "Country")
        value_col = cols.get("value", "Value")
        edu_col = cols.get("%higher_edu_attained", "%higher_edu_attained")
        
        if country and country != "All Countries" and country != "null":
            df = df[df[country_col] == country]
        elif region and region != "All Regions" and region != "null":
            if region in REGION_MAP:
                countries_in_region = REGION_MAP[region]
                df = df[df[country_col].isin(countries_in_region)]

        # Make value numeric
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

        # ---- Create education groups ----
        if edu_col not in df.columns:
             # Fallback if column missing
             return jsonify({"error": "Education column not found"}), 500

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
        
        # Determine colors: Highlight "Low (<10%)" in purple
        # Male (grey #d1d0d0), Female (purple #bb99ff)
        # Purple: #bb99ff, Grey: #d1d0d0
        
        categories = group_avg["edu_group"].tolist()
        values = group_avg[value_col].tolist()
        
        colors = []
        for cat in categories:
            if "Low" in str(cat):
                colors.append("#bb99ff")
            else:
                colors.append("#d1d0d0")

        result = {
            "categories": categories,
            "values": values,
            "colors": colors
        }

        return jsonify(result), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)