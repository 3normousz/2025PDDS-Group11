import db_utils
import pandas as pd

df = db_utils.get_data()
print("Unique values in %higher_edu_attained:")
print(df['%higher_edu_attained'].unique())
