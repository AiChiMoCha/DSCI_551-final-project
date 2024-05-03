import json
import googlemaps

# get geocoding
def geo(apt_info):
    # Extract the place name from mongodb and determine whether it is in the local database. If it is, return the stored longitude and latitude. If not, enter it to the API to obtain it.
    with open('geocoding_results.json', 'r') as f:
        geocoding_results = json.load(f)
    address_list = list(geocoding_results.keys())

    addr = apt_info['Address']
    if addr in address_list:
        geocode_result = geocoding_results[addr]
    else:
        gmaps = googlemaps.Client(key='AIzaSyCogN0Ebg7AyqBjct_CF_qh5qSpQJDH83I')
        geocode_result = gmaps.geocode(addr)
        data = geocode_result[0]['geometry']
        geocode_result = [data['location']['lat'], data['location']['lng']]

    return geocode_result

# Read JSON file line by line, update each line with "geocode" and write back
with open('apartments_odd_1.json', 'r') as f:
    lines = f.readlines()

# Open the file again in write mode
with open('apartments_odd_1.json', 'w') as f:
    for line in lines:
        apt_info = json.loads(line)
        geocode_result = geo(apt_info)
        apt_info['geocode'] = geocode_result
        # Convert dictionary back to JSON string and write to file
        f.write(json.dumps(apt_info) + '\n')

# Read JSON file line by line, update each line with "geocode" and write back
with open('apartments_odd_2.json', 'r') as f:
    lines = f.readlines()

# Open the file again in write mode
with open('apartments_odd_2.json', 'w') as f:
    for line in lines:
        apt_info = json.loads(line)
        geocode_result = geo(apt_info)
        apt_info['geocode'] = geocode_result
        # Convert dictionary back to JSON string and write to file
        f.write(json.dumps(apt_info) + '\n')

# Read JSON file line by line, update each line with "geocode" and write back
with open('apartments_even_1.json', 'r') as f:
    lines = f.readlines()

# Open the file again in write mode
with open('apartments_even_1.json', 'w') as f:
    for line in lines:
        apt_info = json.loads(line)
        geocode_result = geo(apt_info)
        apt_info['geocode'] = geocode_result
        # Convert dictionary back to JSON string and write to file
        f.write(json.dumps(apt_info) + '\n')

# Read JSON file line by line, update each line with "geocode" and write back
with open('apartments_even_2.json', 'r') as f:
    lines = f.readlines()

# Open the file again in write mode
with open('apartments_even_2.json', 'w') as f:
    for line in lines:
        apt_info = json.loads(line)
        geocode_result = geo(apt_info)
        apt_info['geocode'] = geocode_result
        # Convert dictionary back to JSON string and write to file
        f.write(json.dumps(apt_info) + '\n')
