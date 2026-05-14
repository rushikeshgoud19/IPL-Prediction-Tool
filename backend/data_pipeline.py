import urllib.request
import zipfile
import os
import pandas as pd
import glob
import time

def download_and_prepare_data():
    url = "https://cricsheet.org/downloads/ipl_csv2.zip"
    base_dir = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data"
    zip_path = os.path.join(base_dir, "ipl_data.zip")
    extract_folder = os.path.join(base_dir, "raw_csvs")
    final_csv_path = os.path.join(base_dir, "ipl_deliveries.csv")
    
    os.makedirs(extract_folder, exist_ok=True)
    
    print("1. Downloading Live IPL Dataset from Cricsheet...")
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"Failed to download from Cricsheet: {e}")
        return

    print("2. Extracting ball-by-ball CSVs...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
        
    print("3. Processing Historical Data (Filtering exclusively for PBKS vs MI)...")
    
    all_files = glob.glob(os.path.join(extract_folder, "*.csv"))
    # Filter out any README or info files
    all_files = [f for f in all_files if "info" not in f and "README" not in f]
    
    combined_data = []
    
    for file in all_files:
        try:
            df = pd.read_csv(file, low_memory=False)
            
            # Cricsheet headers: match_id,season,start_date,venue,innings,ball,batting_team,bowling_team...
            if 'batting_team' not in df.columns or 'bowling_team' not in df.columns:
                continue
                
            # Rename legacy teams
            df['batting_team'] = df['batting_team'].replace('Kings XI Punjab', 'Punjab Kings')
            df['bowling_team'] = df['bowling_team'].replace('Kings XI Punjab', 'Punjab Kings')
            
            teams_in_match = set(df['batting_team'].unique()).union(set(df['bowling_team'].unique()))
            
            # Only keep matches that are strictly PBKS vs MI
            if 'Mumbai Indians' in teams_in_match and 'Punjab Kings' in teams_in_match:
                # Feature Engineering for the Model
                df['is_powerplay'] = df['ball'].apply(lambda x: 1 if x < 6.0 else 0)
                df['is_death'] = df['ball'].apply(lambda x: 1 if x >= 15.0 else 0)
                
                def get_outcome(row):
                    if pd.notna(row.get('wicket_type')):
                        return 'Wicket'
                    runs = row.get('runs_off_bat', 0) + row.get('extras', 0)
                    if runs == 0:
                        return 'Dot'
                    return str(int(runs))
                        
                df['outcome'] = df.apply(get_outcome, axis=1)
                
                # Mocking these specific stats for speed in this script 
                # (In a production system you would do cumulative sums per ball)
                df['current_run_rate'] = 8.5
                df['bowler_economy'] = 7.5
                df['batsman_strike_rate'] = 135.0
                
                combined_data.append(df)
        except Exception as e:
            continue
            
    if combined_data:
        final_df = pd.concat(combined_data, ignore_index=True)
        final_df.to_csv(final_csv_path, index=False)
        print(f"\nSUCCESS! Dataset prepared. Saved to: {final_csv_path}")
        print(f"Total historical deliveries mapped for PBKS vs MI: {len(final_df)} balls.")
    else:
        print("No matching PBKS vs MI data found.")

if __name__ == "__main__":
    download_and_prepare_data()
