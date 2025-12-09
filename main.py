import os
from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__, static_folder='static')

# Fonts path, you can directly refer to this in your Plotly
glacial_indifference = os.path.join(os.getcwd(), "assets/fonts/", "GlacialIndifference-Regular.otf") 

@app.route("/")
def index():
    try:
        df = pd.read_csv('data/makeovermonday-2020w10/violence_data.csv')

        #subset = df[(df['Gender'] == 'F') & (df['Question'] == '... for at least one specific reason')]
        #subset = df[(df['Gender'] == 'F')]
        subset =  df['Question'] == '... for at least one specific reason'
        percentage = round(subset['Value'].mean(), 1)
        
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
        df = pd.read_csv('data/makeovermonday-2020w10/violence_data.csv')
        
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
        df = pd.read_csv('data/makeovermonday-2020w10/violence_data.csv')

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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)