import pandas as pd
import os
import glob
import numpy as np

def process_matches(raw_dir, output_file):
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    # Filter out info files
    ball_files = [f for f in all_files if "_info" not in f and "README" not in f]
    
    match_records = []
    
    team_map = {
        'Kings XI Punjab': 'Punjab Kings',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Delhi Daredevils': 'Delhi Capitals',
        'Gujarat Lions': 'Gujarat Titans', # Rough mapping for historical consistency if needed, though they are different franchises
    }

    print(f"Processing {len(ball_files)} match files...")

    for file in ball_files:
        try:
            df = pd.read_csv(file, low_memory=False)
            if df.empty: continue
            
            match_id = df['match_id'].iloc[0]
            venue = df['venue'].iloc[0]
            date = df['start_date'].iloc[0]
            
            # Normalize team names
            df['batting_team'] = df['batting_team'].replace(team_map)
            df['bowling_team'] = df['bowling_team'].replace(team_map)
            
            # Group by innings
            innings = df.groupby('innings')
            if len(innings) < 2: continue # Skip incomplete matches
            
            # Innings 1: Team A
            i1 = innings.get_group(1)
            team_a = i1['batting_team'].iloc[0]
            runs_a = i1['runs_off_bat'].sum() + i1['extras'].sum()
            wickets_a = i1['wicket_type'].count()
            
            # Innings 2: Team B
            i2 = innings.get_group(2)
            team_b = i2['batting_team'].iloc[0]
            runs_b = i2['runs_off_bat'].sum() + i2['extras'].sum()
            wickets_b = i2['wicket_type'].count()
            
            # Determine outcome
            # A_small: Team A wins by <= 20 runs or <= 5 wickets
            # A_big: Team A wins by > 20 runs or >= 6 wickets
            # B_small: Team B wins by <= 20 runs or <= 5 wickets
            # B_big: Team B wins by > 20 runs or >= 6 wickets
            
            outcome = None
            if runs_a > runs_b:
                margin_runs = runs_a - runs_b
                if margin_runs > 20:
                    outcome = 'A_big'
                else:
                    outcome = 'A_small'
            elif runs_b > runs_a:
                # Team B wins (chasing)
                # Margin in wickets
                wickets_lost_b = wickets_b
                wickets_won_by = 10 - wickets_lost_b
                if wickets_won_by >= 6:
                    outcome = 'B_big'
                else:
                    outcome = 'B_small'
            else:
                # Tie - handle as A_small or skip
                outcome = 'A_small'
            
            match_records.append({
                'match_id': match_id,
                'date': date,
                'venue': venue,
                'team_a': team_a,
                'team_b': team_b,
                'runs_a': runs_a,
                'runs_b': runs_b,
                'outcome': outcome
            })
            
        except Exception as e:
            # print(f"Error processing {file}: {e}")
            continue
            
    result_df = pd.DataFrame(match_records)
    result_df.to_csv(output_file, index=False)
    print(f"Successfully processed {len(result_df)} matches. Saved to {output_file}")

if __name__ == "__main__":
    raw_directory = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\raw_csvs"
    output_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv"
    process_matches(raw_directory, output_path)
