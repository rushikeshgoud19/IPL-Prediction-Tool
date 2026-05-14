import pandas as pd
from match_outcome_predictor import MatchPredictor

def generate_final_submission():
    predictor = MatchPredictor()
    summary_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv"
    predictor.train(summary_path)
    
    # Target Matches
    targets = [
        {'team_a': 'Sunrisers Hyderabad', 'team_b': 'Kolkata Knight Riders', 'venue': 'Rajiv Gandhi International Stadium, Uppal, Hyderabad', 'match_id': 'SRH_vs_KKR'},
        {'team_a': 'Gujarat Titans', 'team_b': 'Punjab Kings', 'venue': 'Narendra Modi Stadium, Ahmedabad', 'match_id': 'GT_vs_PBKS'},
        {'team_a': 'Mumbai Indians', 'team_b': 'Lucknow Super Giants', 'venue': 'Wankhede Stadium, Mumbai', 'match_id': 'MI_vs_LSG'}
    ]
    
    submission_rows = []
    
    for t in targets:
        # For simplicity, we use 0.5 win rates if not calculated, 
        # but in a real run, the predictor.train() would have stored these.
        # Let's just predict with the model.
        
        preds = predictor.predict_match(t['team_a'], t['team_b'], t['venue'])
        
        row = {
            'match_id': t['match_id'],
            'A_big': preds.get('A_big', 0.25),
            'A_small': preds.get('A_small', 0.25),
            'B_big': preds.get('B_big', 0.25),
            'B_small': preds.get('B_small', 0.25)
        }
        submission_rows.append(row)
        
    sub_df = pd.DataFrame(submission_rows)
    output_path = r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\submission.csv"
    sub_df.to_csv(output_path, index=False)
    print(f"Submission file generated at {output_path}")

if __name__ == "__main__":
    generate_final_submission()
