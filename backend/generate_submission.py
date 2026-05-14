import pandas as pd
import numpy as np
from match_outcome_predictor import MatchPredictor
from prediction_core import BallPredictor
import os

def generate_final_submission():
    """
    Generate the hackathon submission file.
    This creates submission.csv with probabilities for:
    A_big, A_small, B_big, B_small for each target match.
    """
    print("=" * 60)
    print("GENERATING HACKATHON SUBMISSION")
    print("=" * 60)

    # Initialize predictor
    match_summary_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv"
    predictor = MatchPredictor()
    predictor.train(match_summary_path)

    # Target matches (these should match hackathon requirements)
    targets = [
        {
            'team_a': 'Sunrisers Hyderabad',
            'team_b': 'Kolkata Knight Riders',
            'venue': 'Rajiv Gandhi International Stadium, Uppal, Hyderabad',
            'match_id': 'SRH_vs_KKR'
        },
        {
            'team_a': 'Gujarat Titans',
            'team_b': 'Punjab Kings',
            'venue': 'Narendra Modi Stadium, Ahmedabad',
            'match_id': 'GT_vs_PBKS'
        },
        {
            'team_a': 'Mumbai Indians',
            'team_b': 'Lucknow Super Giants',
            'venue': 'Wankhede Stadium, Mumbai',
            'match_id': 'MI_vs_LSG'
        },
        {
            'team_a': 'Royal Challengers Bangalore',
            'team_b': 'Delhi Capitals',
            'venue': 'M Chinnaswamy Stadium, Bengaluru',
            'match_id': 'RCB_vs_DC'
        },
        {
            'team_a': 'Punjab Kings',
            'team_b': 'Chennai Super Kings',
            'venue': 'Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh',
            'match_id': 'PBKS_vs_CSK'
        }
    ]

    submission_rows = []
    print("\n📊 Making predictions for each match...\n")

    for t in targets:
        print(f"Processing: {t['match_id']}")

        try:
            probs = predictor.predict_match(t['team_a'], t['team_b'], t['venue'])

            row = {
                'match_id': t['match_id'],
                'A_big': round(probs.get('A_big', 0.25), 4),
                'A_small': round(probs.get('A_small', 0.25), 4),
                'B_big': round(probs.get('B_big', 0.25), 4),
                'B_small': round(probs.get('B_small', 0.25), 4)
            }

            # Validation: probabilities should sum to ~1
            total = sum([row['A_big'], row['A_small'], row['B_big'], row['B_small']])
            if abs(total - 1.0) > 0.01:
                print(f"  ⚠️ Probabilities sum to {total:.4f}, normalizing...")
                # Normalize
                row = {k: v/total for k, v in row.items()}

            submission_rows.append(row)

            # Print detailed output
            print(f"  {t['team_a']} vs {t['team_b']}")
            print(f"  Venue: {t['venue']}")
            print(f"  Predictions:")
            for outcome, prob in sorted(probs.items(), key=lambda x: -x[1]):
                print(f"    {outcome}: {prob*100:.1f}%")

            # Get team stats
            stats_a = predictor.get_team_stats(t['team_a'])
            stats_b = predictor.get_team_stats(t['team_b'])
            print(f"  {t['team_a']} Win Rate: {stats_a['win_rate']*100:.1f}%")
            print(f"  {t['team_b']} Win Rate: {stats_b['win_rate']*100:.1f}%")

            h2h = predictor.get_h2h_record(t['team_a'], t['team_b'])
            print(f"  H2H Record: {h2h['total']} matches")
            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            # Fallback to equal probabilities
            submission_rows.append({
                'match_id': t['match_id'],
                'A_big': 0.25,
                'A_small': 0.25,
                'B_big': 0.25,
                'B_small': 0.25
            })

    # Create submission DataFrame
    sub_df = pd.DataFrame(submission_rows)

    # Save to CSV
    output_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\submission.csv"
    sub_df.to_csv(output_path, index=False)

    print("=" * 60)
    print("SUBMISSION SUMMARY")
    print("=" * 60)
    print(f"\nFile saved to: {output_path}")
    print(f"\n{sub_df.to_string(index=False)}")

    # Verify probabilities
    print("\n✓ Probability verification (should all be ~0.25 or based on model):")
    for idx, row in sub_df.iterrows():
        total = row['A_big'] + row['A_small'] + row['B_big'] + row['B_small']
        print(f"  {row['match_id']}: sum={total:.4f}")

    return sub_df

if __name__ == "__main__":
    generate_final_submission()