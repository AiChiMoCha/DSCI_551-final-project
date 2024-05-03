import os
import pymongo
import json
import ast

def clean_tags(tags_str):
    """Attempt to correct common JSON string errors in tags and safely parse to list."""
    try:
        # Try to directly evaluate the string to a list
        tags_list = ast.literal_eval(tags_str)
        if isinstance(tags_list, list):
            return tags_list  # Return the list if successfully parsed
    except (SyntaxError, ValueError):
        # If there is a syntax error in the initial parse attempt, handle manually
        try:
            # Replace problematic characters and attempt to parse again
            tags_str = tags_str.replace("', '", "','").replace(" '", "'").replace(",'", "','").replace(" '", "'")
            tags_list = ast.literal_eval(tags_str)
            if isinstance(tags_list, list):
                return tags_list
        except:
            # If still failing, split manually assuming comma separation
            tags_list = [tag.strip().strip("'") for tag in tags_str.strip('[]').split(',')]
            return tags_list
    return []  # Return an empty list if all attempts fail

def upload_json_to_mongodb(json_file_path, collection_name):
    # MongoDB connection
    client = pymongo.MongoClient(host="localhost", port=27017)
    db = client['finalProject_db']  # Connect to the specified database
    collection = db[collection_name]

    # Read JSON and import each line
    with open(json_file_path, 'r') as file:
        for line in file:
            try:
                file_data = json.loads(line)  # Parse each line as JSON

                # Ensure Tags field is a list
                if 'Tags' in file_data and isinstance(file_data['Tags'], str):
                    file_data['Tags'] = clean_tags(file_data['Tags'])

                collection.insert_one(file_data)  # Attempt to insert each object
            except json.JSONDecodeError as e:
                print(f"JSON decode error in {json_file_path}: {e}")
            except pymongo.errors.DuplicateKeyError:
                print(f"Duplicate entry found in {json_file_path}, skipping.")
            except Exception as e:
                print(f"An error occurred with {file_data.get('_id', 'Unknown')}: {e}")

    print(f'Data from {json_file_path} has been imported to {collection_name} collection.')

if __name__ == '__main__':
    # Define paths and collection names
    files_and_collections = {
        'apartments_even_1.json': 'apartments_even_1',
        'apartments_odd_1.json': 'apartments_odd_1',
        'apartments_even_2.json': 'apartments_even_2',
        'apartments_odd_2.json': 'apartments_odd_2'
    }
    
    # Iterate through the mapping and upload each file
    for json_file, collection_name in files_and_collections.items():
        upload_json_to_mongodb(json_file, collection_name)

