import pandas as pd
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, filename='data_merge.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define the data directory
data_dir = 'data'

# List all CSV files in the data directory
files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

# Remove the zip file from the list if it exists
zip_file = 'dpt_2000_2021_csv.zip'
if zip_file in files:
    files.remove(zip_file)
    logging.info(f'Removed zip file from the list: {zip_file}')

# Initialize a list to hold DataFrames
data_frames = []

# Read each file and append to the list of DataFrames if it contains data
for file in files:
    file_path = os.path.join(data_dir, file)
    try:
        df = pd.read_csv(file_path)
        if not df.empty:
            data_frames.append(df)
            logging.info(f'Read file: {file}')
        else:
            logging.warning(f'{file} is empty and will be skipped.')
    except Exception as e:
        logging.error(f'Error reading {file}: {e}')

# Check if there are DataFrames to concatenate
if data_frames:
    try:
        df = pd.concat(data_frames, ignore_index=True)
        logging.info('Concatenation successful.')
    except Exception as e:
        logging.error(f'Error concatenating data: {e}')
    else:
        # Save the merged DataFrame to a CSV file
        try:
            output_path = os.path.join(data_dir, 'merged_data.csv')
            df.to_csv(output_path, index=False)
            logging.info(f'Merged data saved to {output_path}')
        except Exception as e:
            logging.error(f'Error saving merged data to CSV: {e}')

        # Remove the individual files after successful merge
        for file in files:
            file_path = os.path.join(data_dir, file)
            try:
                os.remove(file_path)
                logging.info(f'Removed file: {file}')
            except Exception as e:
                logging.error(f'Error removing {file}: {e}')
else:
    logging.warning('No valid data files found to concatenate.')
