import pandas as pd
import glob
import os

def download_and_prepare_data():
    """
    Downloads and processes IPL ball-by-ball data.
    Computes REAL features instead of hardcoded values.
    """
    base_dir = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data"
    extract_folder = os.path.join(base_dir, "raw_csvs")
    final_csv_path = os.path.join(base_dir, "ipl_deliveries.csv")

    os.makedirs(extract_folder, exist_ok=True)

    print("1. Loading ball-by-ball data from Cricsheet...")

    all_files = glob.glob(os.path.join(extract_folder, "*.csv"))
    # Filter out info files
    all_files = [f for f in all_files if "_info" not in f and "README" not in f and "match_summary" not in f]

    combined_data = []

    # Team name normalization
    team_map = {
        'Kings XI Punjab': 'Punjab Kings',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Delhi Daredevils': 'Delhi Capitals',
        'Gujarat Lions': 'Gujarat Titans',
    }

    print(f"   Found {len(all_files)} match files")

    for idx, file in enumerate(all_files):
        if idx % 100 == 0:
            print(f"   Processing file {idx+1}/{len(all_files)}...")

        try:
            df = pd.read_csv(file, low_memory=False)

            # Skip if missing required columns
            required_cols = ['batting_team', 'bowling_team', 'ball', 'runs_off_bat', 'extras']
            if not all(col in df.columns for col in required_cols):
                continue

            # Normalize team names
            df['batting_team'] = df['batting_team'].replace(team_map)
            df['bowling_team'] = df['bowling_team'].replace(team_map)

            # Initialize columns
            df['is_powerplay'] = 0
            df['is_death'] = 0

            # Sort by ball number to ensure proper order
            df = df.sort_values(['innings', 'ball']).reset_index(drop=True)

            # Group by innings for cumulative calculations
            for innings_group in df.groupby('innings'):
                innings_df = innings_group[1].copy()
                match_id = innings_df['match_id'].iloc[0]

                # Calculate cumulative runs and balls for run rate
                innings_df['cumulative_runs'] = innings_df['runs_off_bat'].cumsum().shift(1).fillna(0)
                innings_df['balls_bowled'] = range(1, len(innings_df) + 1)

                # Calculate over number (ball 0.1 = over 1, ball 1.1 = over 2, etc.)
                def get_over_number(ball):
                    over = int(ball) + 1
                    ball_in_over = round((ball - int(ball)) * 10)
                    return over + ball_in_over / 10

                innings_df['over_num'] = innings_df['ball'].apply(get_over_number)

                # Current run rate = (runs so far / overs completed)
                innings_df['current_run_rate'] = innings_df.apply(
                    lambda row: (row['cumulative_runs'] / row['over_num'] * 6) if row['over_num'] > 0 else 0,
                    axis=1
                )

                # Powerplay (overs 1-6) and Death (overs 16-20)
                innings_df['is_powerplay'] = innings_df['ball'].apply(lambda x: 1 if x < 6.0 else 0)
                innings_df['is_death'] = innings_df['ball'].apply(lambda x: 1 if x >= 15.0 else 0)

                combined_data.append(innings_df)

        except Exception as e:
            continue

    if not combined_data:
        print("ERROR: No data was processed!")
        return

    final_df = pd.concat(combined_data, ignore_index=True)

    # Calculate bowler economy (runs per over for this specific bowler in this innings)
    def calculate_bowler_economy(group):
        bowler_economies = []
        for idx, row in group.iterrows():
            bowler = row['bowler']
            # Get all balls this bowler has bowled up to this point
            prior_balls = group[(group['bowler'] == bowler) & (group.index < idx)]
            if len(prior_balls) > 0:
                runs_conceded = prior_balls['runs_off_bat'].sum() + prior_balls['extras'].sum()
                balls_bowled = len(prior_balls)
                economy = (runs_conceded / balls_bowled) * 6 if balls_bowled > 0 else 8.0
            else:
                economy = 8.0  # Default
            bowler_economies.append(economy)
        return pd.Series(bowler_economies, index=group.index)

    # Calculate batsman strike rate
    def calculate_batsman_sr(group):
        batsman_srs = []
        for idx, row in group.iterrows():
            striker = row['striker']
            prior_balls = group[(group['striker'] == striker) & (group.index < idx)]
            if len(prior_balls) > 0:
                runs_scored = prior_balls['runs_off_bat'].sum()
                balls_faced = len(prior_balls)
                sr = (runs_scored / balls_faced) * 100 if balls_faced > 0 else 130.0
            else:
                sr = 130.0  # Default
            batsman_srs.append(sr)
        return pd.Series(batsman_srs, index=group.index)

    print("   Computing bowler economy and batsman strike rate...")

    # Apply per innings
    for innings_group in final_df.groupby('innings'):
        mask = final_df['innings'] == innings_group[0]
        final_df.loc[mask, 'bowler_economy'] = calculate_bowler_economy(final_df[mask])
        final_df.loc[mask, 'batsman_strike_rate'] = calculate_batsman_sr(final_df[mask])

    # Fill any missing values
    final_df['bowler_economy'] = final_df['bowler_economy'].fillna(8.0)
    final_df['batsman_strike_rate'] = final_df['batsman_strike_rate'].fillna(130.0)
    final_df['current_run_rate'] = final_df['current_run_rate'].fillna(0)

    # Create outcome column
    def get_outcome(row):
        if pd.notna(row.get('wicket_type')):
            return 'Wicket'
        runs = row.get('runs_off_bat', 0)
        if runs == 0:
            return 'Dot'
        return str(int(runs))

    final_df['outcome'] = final_df.apply(get_outcome, axis=1)

    # Select and reorder columns for the model
    output_cols = [
        'match_id', 'season', 'start_date', 'venue',
        'innings', 'ball',
        'batting_team', 'bowling_team',
        'striker', 'non_striker', 'bowler',
        'runs_off_bat', 'extras',
        'wicket_type',
        'is_powerplay', 'is_death',
        'current_run_rate', 'bowler_economy', 'batsman_strike_rate',
        'outcome'
    ]

    # Only keep columns that exist
    output_cols = [c for c in output_cols if c in final_df.columns]
    final_df = final_df[output_cols]

    # Save to CSV
    final_df.to_csv(final_csv_path, index=False)

    print(f"\n✅ SUCCESS! Dataset prepared with REAL features.")
    print(f"   Total deliveries: {len(final_df)}")
    print(f"   Matches covered: {final_df['match_id'].nunique()}")
    print(f"   Saved to: {final_csv_path}")

    # Print feature stats
    print("\n   Feature Statistics:")
    print(f"   - Current Run Rate: mean={final_df['current_run_rate'].mean():.2f}, std={final_df['current_run_rate'].std():.2f}")
    print(f"   - Bowler Economy: mean={final_df['bowler_economy'].mean():.2f}, std={final_df['bowler_economy'].std():.2f}")
    print(f"   - Batsman SR: mean={final_df['batsman_strike_rate'].mean():.2f}, std={final_df['batsman_strike_rate'].std():.2f}")

    # Outcome distribution
    print("\n   Outcome Distribution:")
    print(final_df['outcome'].value_counts(normalize=True).head(10).apply(lambda x: f"{x*100:.1f}%"))

if __name__ == "__main__":
    download_and_prepare_data()