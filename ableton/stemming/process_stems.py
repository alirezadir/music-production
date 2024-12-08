import os
import sys
import subprocess  # This line was missing
import requests

# Define the API key and the base URL for the Lalal.ai API
API_KEY = '3116e7fde1a140ac'
LALALAI_API_URL = 'https://api.lalal.ai/v1/process'


# Get the file path from the command line argument
file_path = sys.argv[1]
input_directory = os.path.dirname(file_path)
output_directory = os.path.join(input_directory, 'stems-lalalai')

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Define the list of stem types in the desired order
stem_types = [
    'vocals', 
    'drum', 
    'bass', 
    'piano', 
    'electric_guitar', 
    'acoustic_guitar', 
    'synthesizer', 
    'voice', 
    'strings', 
    'wind'
]

# Function to process the file
def process_file(file_path):
    file_name = os.path.basename(file_path)
    file_stems_directory = os.path.join(output_directory, os.path.splitext(file_name)[0])
    os.makedirs(file_stems_directory, exist_ok=True)
    
    for stem_type in stem_types:
        # Make the API call to Lalal.ai for the specific stem
        response = requests.post(
            LALALAI_API_URL,
            headers={'Authorization': f'Bearer ' + API_KEY},
            files={'file': open(file_path, 'rb')},
            data={'stem': stem_type}
        )
        
        if response.status_code == 200:
            # Save the stem file in the output directory
            stem_file_path = os.path.join(file_stems_directory, f'{stem_type}.wav')
            with open(stem_file_path, 'wb') as stem_file:
                stem_file.write(response.content)
            print(f'Successfully saved {stem_type} stem for {file_name}')
        else:
            print(f'Failed to process {stem_type} stem for {file_name}. Error: {response.text}')

# Process the file
process_file(file_path)

print('Stemming process completed.')