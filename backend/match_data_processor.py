import pandas as pd
import os
import glob
import numpy as np

# Normalize venue names to handle variations
VENUE_MAP = {
    'Rajiv Gandhi International Stadium, Uppal': 'Rajiv Gandhi International Stadium, Uppal, Hyderabad',
    'Rajiv Gandhi International Stadium': 'Rajiv Gandhi International Stadium, Uppal, Hyderabad',
    'M.Chinnaswamy Stadium': 'M Chinnaswamy Stadium, Bengaluru',
    'M Chinnaswamy Stadium': 'M Chinnaswamy Stadium, Bengaluru',
    'MA Chidambaram Stadium, Chepauk': 'MA Chidambaram Stadium, Chepauk, Chennai',
    'MA Chidambaram Stadium': 'MA Chidambaram Stadium, Chepauk, Chennai',
    'Feroz Shah Kotla': 'Arun Jaitley Stadium, Delhi',
    'Feroz Shah Kotla, Delhi': 'Arun Jaitley Stadium, Delhi',
    'Arun Jaitley Stadium': 'Arun Jaitley Stadium, Delhi',
    'Saurashtra Cricket Association Stadium': 'Saurashtra Cricket Association Stadium, Rajkot',
    'Sawai Mansingh Stadium': 'Sawai Mansingh Stadium, Jaipur',
    'Punjab Cricket Association IS Bindra Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh',
    'Punjab Cricket Association Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh',
    'Punjab Cricket Association IS Bindra Stadium': 'Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh',
    'Punjab Cricket Association IS Bindra Stadium, New Chandigarh': 'Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur',
    'Punjab Cricket Association IS Bindra Stadium, Mullanpur': 'Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur',
    'Nehru Stadium': 'Maharashtra Cricket Association Stadium, Pune',
    'Dr DY Patil Sports Academy': 'Dr DY Patil Sports Academy, Mumbai',
    'De Beers Diamond Oval': 'De Beers Diamond Oval, Kimberley',
    'New Wanderers Stadium': 'Bulls Eye',
    'Kingsmead': 'Kingsmead, Durban',
    'SuperSport Park': 'SuperSport Park, Centurion',
    'Newlands': 'Newlands, Cape Town',
    'St George\'s Park': 'St George\'s Park, Gqeberha',
    'Buffalo Park': 'Buffalo Park, East London',
    'OUTsurance Oval': 'OUTsurance Oval, Bloemfontein',
    'Sheikh Zayed Stadium': 'Sheikh Zayed Stadium, Abu Dhabi',
    'Zayed Cricket Stadium': 'Sheikh Zayed Stadium, Abu Dhabi',
    'Dubai International Cricket Stadium': 'Dubai International Cricket Stadium, Dubai',
    'Sharjah Cricket Stadium': 'Sharjah Cricket Stadium, Sharjah',
    'Brabourne Stadium': 'Brabourne Stadium, Mumbai',
    'Subrata Roy Sahara Stadium': 'Subrata Roy Sahara Stadium, Pune',
    'Green Park': 'Green Park Stadium, Kanpur',
    'Barabati Stadium': 'Barabati Stadium, Cuttack',
    'Vidarbha Cricket Association Stadium, Jamtha': 'Vidarbha Cricket Association Stadium, Jamtha, Nagpur',
    'JSCA International Stadium Complex': 'JSCA International Stadium Complex, Ranchi',
}

def normalize_venue(venue):
    """Normalize venue name to standard form"""
    if pd.isna(venue):
        return 'Unknown Venue'
    venue = str(venue).strip()
    # Check if in our map
    if venue in VENUE_MAP:
        return VENUE_MAP[venue]
    # Already normalized or not in map - return as is
    return venue

def process_matches(raw_dir, output_file):
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    # Filter out info files
    ball_files = [f for f in all_files if "_info" not in f and "README" not in f]

    match_records = []

    team_map = {
        'Kings XI Punjab': 'Punjab Kings',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Delhi Daredevils': 'Delhi Capitals',
        'Gujarat Lions': 'Gujarat Titans',
    }

    venue_stats = {}  # Track avg runs per venue for feature engineering

    print(f"Processing {len(ball_files)} match files...")

    for file in ball_files:
        try:
            df = pd.read_csv(file, low_memory=False)
            if df.empty: continue

            match_id = df['match_id'].iloc[0]
            venue_raw = df['venue'].iloc[0]
            venue = normalize_venue(venue_raw)
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

            # Track venue stats for average score calculation
            avg_score = (runs_a + runs_b) / 2
            if venue not in venue_stats:
                venue_stats[venue] = []
            venue_stats[venue].append(avg_score)

            # Determine outcome based on margin
            # A_big: Team A wins by > 20 runs OR >= 6 wickets
            # A_small: Team A wins by <= 20 runs AND < 6 wickets
            # B_big: Team B wins by > 20 runs OR >= 6 wickets
            # B_small: Team B wins by <= 20 runs AND < 6 wickets

            outcome = None
            if runs_a > runs_b:
                margin_runs = runs_a - runs_b
                # Assuming Team B chased - margin in wickets lost
                wickets_lost_a = wickets_a
                wickets_won_by_a = 10 - wickets_lost_a

                if margin_runs > 20 or wickets_won_by_a >= 6:
                    outcome = 'A_big'
                else:
                    outcome = 'A_small'
            elif runs_b > runs_a:
                # Team B wins (chasing)
                wickets_lost_b = wickets_b
                wickets_won_by_b = 10 - wickets_lost_b

                if margin_runs := runs_b - runs_a > 20 or wickets_won_by_b >= 6:
                    outcome = 'B_big'
                else:
                    outcome = 'B_small'
            else:
                # Tie - assign to B_small
                outcome = 'B_small'

            match_records.append({
                'match_id': match_id,
                'date': date,
                'venue': venue,
                'team_a': team_a,
                'team_b': team_b,
                'runs_a': runs_a,
                'runs_b': runs_b,
                'wickets_a': wickets_a,
                'wickets_b': wickets_b,
                'outcome': outcome
            })

        except Exception as e:
            # print(f"Error processing {file}: {e}")
            continue

    result_df = pd.DataFrame(match_records)

    # Add venue average score as a feature
    result_df['venue_avg_score'] = result_df['venue'].map(
        lambda v: np.mean(venue_stats.get(v, [160])) if v in venue_stats else 160
    )

    # Add year feature for time decay
    result_df['year'] = pd.to_datetime(result_df['date']).dt.year

    result_df.to_csv(output_file, index=False)

    print(f"Successfully processed {len(result_df)} matches. Saved to {output_file}")
    print(f"Unique venues: {result_df['venue'].nunique()}")
    print(f"Outcome distribution:")
    print(result_df['outcome'].value_counts())

    # Print all unique venues for verification
    print("\nVenue normalization results:")
    for v in sorted(result_df['venue'].unique()):
        count = len(result_df[result_df['venue'] == v])
        print(f"  {v}: {count} matches")

if __name__ == "__main__":
    raw_directory = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\raw_csvs"
    output_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv"
    process_matches(raw_directory, output_path)