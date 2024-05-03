import pandas as pd
import re

def hash_name(name):
    """Distribute names into four collections based on the first character."""
    # Normalize the name
    normalized_name = name.strip().lower()
    
    # Determine collection index based on the first character
    if normalized_name[0] in 'abcd':
        return 0
    elif normalized_name[0] in 'efgh':
        return 1
    elif normalized_name[0] in 'ijkl':
        return 2
    else:
        return 3

def parse_rating(rating):
    """Parse rating and extract average score and number of reviews."""
    if pd.isnull(rating) or rating == "":
        return {"avg": 0, "num": 0}
    match = re.search(r"(\d+(?:\.\d+)?)(?:\((\d+)\))?", rating)
    if match:
        avg = float(match.group(1))
        num = int(match.group(2)) if match.group(2) else 0
        return {"avg": avg, "num": num}
    return {"avg": 0, "num": 0}

# Read raw data files
df = pd.read_csv('merged_rentals.csv')

# Rename columns
df.rename(columns={
    "Unnamed: 3": "room_types_prices",
    "Unnamed: 5": "travel_times"
}, inplace=True)

# Apply hash function to determine collection
df['collection_index'] = df['Name'].apply(hash_name)
df['_id'] = df['Name']

# Parse the Rating column
df['Rating'] = df['Rating'].apply(parse_rating)

# Split data frame based on hash result
df_0 = df[df['collection_index'] == 0].drop(columns=['collection_index'])
df_1 = df[df['collection_index'] == 1].drop(columns=['collection_index'])
df_2 = df[df['collection_index'] == 2].drop(columns=['collection_index'])
df_3 = df[df['collection_index'] == 3].drop(columns=['collection_index'])

# Export to JSON
df_0.to_json('apartments_even_1.json', orient='records', lines=True)
df_1.to_json('apartments_odd_1.json', orient='records', lines=True)
df_2.to_json('apartments_even_2.json', orient='records', lines=True)
df_3.to_json('apartments_odd_2.json', orient='records', lines=True)

print("JSON files have been generated successfully")
