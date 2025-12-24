import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_data():
    conn = get_db_connection()
    
    query = '''
    SELECT 
        r.Record_ID as recordID,
        c.Country_name as country,
        c.High_edu_stt as high_edu_stt,
        d.Gender as gender,
        d.Age_Group,
        d.Marital_Status,
        d.Education,
        d.Employment,
        d.Residence,
        q.Ques_detail as question,
        r.Value as value
    FROM Record r
    JOIN Country c ON r.Country_ID = c.Country_ID
    JOIN Demographic_Group d ON r.Dem_ID = d.Dem_ID
    JOIN Question q ON r.Ques_ID = q.Ques_ID
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Maps from column name to demo_question value
    demo_map = {
        'Age_Group': 'Age',
        'Marital_Status': 'Marital status',
        'Education': 'Education',
        'Employment': 'Employment',
        'Residence': 'Residence'
    }
    
    def get_demo_info(row):
        for col, question_text in demo_map.items():
            if pd.notna(row[col]):
                return question_text, row[col]
        return None, None

    # Melt the DataFrame to long format for demo_question and demo_response
    id_vars = ['recordID', 'country', 'high_edu_stt', 'gender', 'question', 'value']
    value_vars = list(demo_map.keys())
    
    melted = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='demo_col', value_name='demo_response')
    
    # Filter out rows where demo_response is NaN
    melted = melted.dropna(subset=['demo_response'])
    
    # Map demo_col to demo_question
    melted['demo_question'] = melted['demo_col'].map(demo_map)
    
    # Rename high_edu_stt to %higher_edu_attained to match CSV version
    melted = melted.rename(columns={'high_edu_stt': '%higher_edu_attained'})
    
    # Select and reorder columns to match CSV version
    final_cols = ['recordID', 'country', 'gender', 'demo_question', 'demo_response', 'question', 'value', '%higher_edu_attained']
    
    return melted[final_cols]

if __name__ == "__main__":
    # Test data retrieval independently
    df = get_data()
    print(df.head())
    print(f"Shape: {df.shape}")
