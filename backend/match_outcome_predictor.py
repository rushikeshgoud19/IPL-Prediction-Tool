import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss
import pickle
import os

class MatchPredictor:
    def __init__(self):
        self.team_le = LabelEncoder()
        self.venue_le = LabelEncoder()
        self.model = None
        self.classes = ['A_big', 'A_small', 'B_big', 'B_small']
        
    def prepare_features(self, df):
        # Sort by date
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Cumulative Win Rates
        team_stats = {}
        h2h_stats = {}
        
        features = []
        
        for idx, row in df.iterrows():
            ta = row['team_a']
            tb = row['team_b']
            
            # Get current stats before this match
            wr_a = team_stats.get(ta, [0, 0]) # [wins, total]
            wr_b = team_stats.get(tb, [0, 0])
            
            h2h_key = tuple(sorted([ta, tb]))
            h2h = h2h_stats.get(h2h_key, {ta: 0, tb: 0, 'total': 0})
            
            feat = {
                'team_a': ta,
                'team_b': tb,
                'venue': row['venue'],
                'wr_a': wr_a[0] / wr_a[1] if wr_a[1] > 0 else 0.5,
                'wr_b': wr_b[0] / wr_b[1] if wr_b[1] > 0 else 0.5,
                'h2h_wr_a': h2h[ta] / h2h['total'] if h2h['total'] > 0 else 0.5,
                'outcome': row['outcome'],
                'date': row['date']
            }
            features.append(feat)
            
            # Update stats after match
            winner = None
            if 'A' in row['outcome']: winner = ta
            else: winner = tb
            
            team_stats[ta] = team_stats.get(ta, [0, 0])
            team_stats[ta][1] += 1
            if winner == ta: team_stats[ta][0] += 1
            
            team_stats[tb] = team_stats.get(tb, [0, 0])
            team_stats[tb][1] += 1
            if winner == tb: team_stats[tb][0] += 1
            
            h2h_stats[h2h_key] = h2h_stats.get(h2h_key, {ta: 0, tb: 0, 'total': 0})
            h2h_stats[h2h_key]['total'] += 1
            h2h_stats[h2h_key][winner] += 1
            
        feat_df = pd.DataFrame(features)
        return feat_df

    def train(self, summary_csv):
        df = pd.read_csv(summary_csv)
        feat_df = self.prepare_features(df)
        
        # Encode teams and venues
        all_teams = pd.concat([feat_df['team_a'], feat_df['team_b']]).unique()
        self.team_le.fit(all_teams)
        self.venue_le.fit(feat_df['venue'].unique())
        
        feat_df['team_a_enc'] = self.team_le.transform(feat_df['team_a'])
        feat_df['team_b_enc'] = self.team_le.transform(feat_df['team_b'])
        feat_df['venue_enc'] = self.venue_le.transform(feat_df['venue'])
        
        X = feat_df[['team_a_enc', 'team_b_enc', 'venue_enc', 'wr_a', 'wr_b', 'h2h_wr_a']]
        y = feat_df['outcome']
        
        # Split for validation (e.g., matches before 2026-05-01)
        split_date = pd.to_datetime('2026-05-01')
        train_idx = feat_df['date'] < split_date
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[~train_idx], y[train_idx] # Dummy for structure
        
        # Calibrated model for Log Loss
        base_rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
        self.model = CalibratedClassifierCV(base_rf, method='sigmoid', cv=5)
        self.model.fit(X_train, y_train)
        
        print("Model trained and calibrated.")
        
    def predict_match(self, team_a, team_b, venue, wr_a=0.5, wr_b=0.5, h2h_wr_a=0.5):
        ta_enc = self.team_le.transform([team_a])[0]
        tb_enc = self.team_le.transform([team_b])[0]
        v_enc = self.venue_le.transform([venue])[0]
        
        X = [[ta_enc, tb_enc, v_enc, wr_a, wr_b, h2h_wr_a]]
        probs = self.model.predict_proba(X)[0]
        
        return dict(zip(self.model.classes_, probs))

if __name__ == "__main__":
    predictor = MatchPredictor()
    predictor.train(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv")
    
    # Example: SRH vs KKR at Hyderabad
    # I should ideally fetch the current wr and h2h from the processed data
    print("Prediction for SRH vs KKR:", predictor.predict_match('Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Rajiv Gandhi International Stadium, Uppal, Hyderabad'))
