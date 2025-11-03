import pandas as pd
import re

# Load CSV file
df = pd.read_csv("연세한국어 문법 2급.csv", sep="|")

# Define a function to clean the Korean column
def format_dialogue(text):
    # Replace ' / 나:' or ' 나:' with '<br>나:'
    text = re.sub(r'\s*/?\s*나:', ' \n나:', text)
    # Replace ' / B:' or ' B:' with '<br>B:'
    text = re.sub(r'\s*/?\s*B:', ' \nB:', text)
    return text

# Apply the function to the Korean column
df['Korean'] = df['Korean'].apply(format_dialogue)
df['English'] = df['English'].apply(format_dialogue)

# Save the updated file
df.to_csv("연세한국어 문법 2급_modified.csv", index=False, sep="|")
