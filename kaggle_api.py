"""
IPL Match Predictor - Kaggle Compatible API
==========================================
Run this as a Kaggle Notebook or deploy via Kaggle API

Usage in Kaggle Notebook:
    !pip install flask flask-cors
    %run kaggle_api.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.calibration import CalibratedClassifierCV
import warnings
import json
import os
warnings.filterwarnings('ignore')

# ============================================================================
# MATCH PREDICTOR MODEL
# ============================================================================

class MatchPredictor:
    """High-accuracy IPL match outcome predictor"""

    def __init__(self):
        self.team_le = LabelEncoder()
        self.venue_le = LabelEncoder()
        self.scaler = StandardScaler()
        self.classes = ['A_big', 'A_small', 'B_big', 'B_small']
        self.team_stats = {}
        self.h2h_stats = {}
        self.venue_stats = {}
        self.form_stats = {}
        self.models = {}
        self.margin_model = None
        self.is_trained = False

    def get_momentum(self, team):
        if team not in self.form_stats or len(self.form_stats[team]) < 3:
            return 0
        return sum(self.form_stats[team][-3:])

    def prepare_features(self, df):
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        all_teams = pd.concat([df['team_a'], df['team_b']]).unique()
        self.team_le.fit(all_teams)
        self.venue_le.fit(df['venue'].unique())

        df['team_a_enc'] = self.team_le.transform(df['team_a'])
        df['team_b_enc'] = self.team_le.transform(df['team_b'])
        df['venue_enc'] = self.venue_le.transform(df['venue'])

        wr_a_list, wr_b_list = [], []
        h2h_wr_a_list, venue_wr_a_list = [], []
        recent_a_list, recent_b_list = [], []
        momentum_a_list, momentum_b_list = [], []
        streak_a_list, streak_b_list = [], []

        for idx, row in df.iterrows():
            ta, tb, venue = row['team_a'], row['team_b'], row['venue']

            ts_a = self.team_stats.get(ta, [0, 0])
            ts_b = self.team_stats.get(tb, [0, 0])
            wr_a = ts_a[0] / ts_a[1] if ts_a[1] > 0 else 0.5
            wr_b = ts_b[0] / ts_b[1] if ts_b[1] > 0 else 0.5

            h2h_key = tuple(sorted([ta, tb]))
            h2h = self.h2h_stats.get(h2h_key, {ta: 0, tb: 0, 'total': 0})
            h2h_wr_a = h2h[ta] / h2h['total'] if h2h['total'] > 0 else 0.5

            vs_key = tuple(sorted([ta, venue]))
            vs_venue = self.venue_stats.get(vs_key, {ta: 0, 'total': 0})
            venue_wr_a = vs_venue[ta] / vs_venue['total'] if vs_venue['total'] > 0 else 0.5

            fs_a = self.form_stats.get(ta, [])
            fs_b = self.form_stats.get(tb, [])
            recent_a = np.mean(fs_a[-5:]) if fs_a else 0.5
            recent_b = np.mean(fs_b[-5:]) if fs_b else 0.5

            momentum_a = self.get_momentum(ta)
            momentum_b = self.get_momentum(tb)

            streak_a = 0
            for w in reversed(fs_a[-10:]):
                if w == 1: streak_a += 1
                else: break
            streak_b = 0
            for w in reversed(fs_b[-10:]):
                if w == 1: streak_b += 1
                else: break

            wr_a_list.append(wr_a)
            wr_b_list.append(wr_b)
            h2h_wr_a_list.append(h2h_wr_a)
            venue_wr_a_list.append(venue_wr_a)
            recent_a_list.append(recent_a)
            recent_b_list.append(recent_b)
            momentum_a_list.append(momentum_a)
            momentum_b_list.append(momentum_b)
            streak_a_list.append(streak_a)
            streak_b_list.append(streak_b)

            winner = ta if 'A' in row['outcome'] else tb

            for team in [ta, tb]:
                if team not in self.team_stats:
                    self.team_stats[team] = [0, 0]
                self.team_stats[team][1] += 1
                if winner == team:
                    self.team_stats[team][0] += 1

            for team in [ta, tb]:
                if team not in self.form_stats:
                    self.form_stats[team] = []
                self.form_stats[team].append(1 if winner == team else 0)
                self.form_stats[team] = self.form_stats[team][-50:]

            if h2h_key not in self.h2h_stats:
                self.h2h_stats[h2h_key] = {ta: 0, tb: 0, 'total': 0}
            self.h2h_stats[h2h_key]['total'] += 1
            self.h2h_stats[h2h_key][winner] = self.h2h_stats[h2h_key].get(winner, 0) + 1

            if vs_key not in self.venue_stats:
                self.venue_stats[vs_key] = {ta: 0, 'total': 0}
            self.venue_stats[vs_key]['total'] += 1
            if winner == ta:
                self.venue_stats[vs_key][ta] = self.venue_stats[vs_key].get(ta, 0) + 1

        df['wr_a'] = wr_a_list
        df['wr_b'] = wr_b_list
        df['h2h_wr_a'] = h2h_wr_a_list
        df['venue_wr_a'] = venue_wr_a_list
        df['recent_a'] = recent_a_list
        df['recent_b'] = recent_b_list
        df['momentum_a'] = momentum_a_list
        df['momentum_b'] = momentum_b_list
        df['streak_a'] = streak_a_list
        df['streak_b'] = streak_b_list
        df['wr_diff'] = df['wr_a'] - df['wr_b']
        df['form_diff'] = df['recent_a'] - df['recent_b']
        df['h2h_advantage'] = df['h2h_wr_a'] - 0.5
        df['momentum_diff'] = df['momentum_a'] - df['momentum_b']
        df['streak_diff'] = df['streak_a'] - df['streak_b']

        return df

    def train(self, summary_csv):
        print("=" * 60)
        print("[MatchPredictor] Loading data...")
        print("=" * 60)

        df = pd.read_csv(summary_csv)
        print(f"[MatchPredictor] Loaded {len(df)} matches")

        feat_df = self.prepare_features(df)

        feature_cols = ['team_a_enc', 'team_b_enc', 'venue_enc',
                        'wr_a', 'wr_b', 'h2h_wr_a', 'venue_wr_a',
                        'recent_a', 'recent_b', 'momentum_a', 'momentum_b',
                        'streak_a', 'streak_b',
                        'wr_diff', 'form_diff', 'h2h_advantage',
                        'momentum_diff', 'streak_diff']

        X = feat_df[feature_cols].values
        self.y_winner = feat_df['outcome'].apply(lambda x: 0 if x in ['A_big', 'A_small'] else 1).values
        self.y_margin = feat_df['outcome'].apply(lambda x: 1 if x in ['A_big', 'B_big'] else 0).values

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.feature_cols = feature_cols

        print("[MatchPredictor] Training ensemble (4 models)...")

        rf = CalibratedClassifierCV(
            RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=3,
                                   class_weight='balanced', random_state=42, n_jobs=-1),
            method='sigmoid', cv=5)

        gb = CalibratedClassifierCV(
            GradientBoostingClassifier(n_estimators=300, max_depth=8, learning_rate=0.05,
                                       min_samples_split=5, random_state=42),
            method='sigmoid', cv=5)

        et = CalibratedClassifierCV(
            ExtraTreesClassifier(n_estimators=500, max_depth=20, min_samples_split=3,
                                class_weight='balanced', random_state=42, n_jobs=-1),
            method='sigmoid', cv=5)

        lr = CalibratedClassifierCV(
            LogisticRegression(class_weight='balanced', max_iter=1000, C=0.5, random_state=42),
            method='sigmoid', cv=5)

        rf.fit(X_scaled, self.y_winner)
        gb.fit(X_scaled, self.y_winner)
        et.fit(X_scaled, self.y_winner)
        lr.fit(X_scaled, self.y_winner)

        self.models = {'rf': rf, 'gb': gb, 'et': et, 'lr': lr}

        self.margin_model = GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
        self.margin_model.fit(X_scaled, self.y_margin)

        self.is_trained = True
        print("[MatchPredictor] Training complete!")
        return self

    def predict_match(self, team_a, team_b, venue):
        if not self.is_trained:
            return {c: 0.25 for c in self.classes}

        try:
            ta_enc = self.team_le.transform([team_a])[0]
            tb_enc = self.team_le.transform([team_b])[0]
            v_enc = self.venue_le.transform([venue])[0]

            ts_a = self.team_stats.get(team_a, [0, 1])
            ts_b = self.team_stats.get(team_b, [0, 1])
            h2h_key = tuple(sorted([team_a, team_b]))
            h2h = self.h2h_stats.get(h2h_key, {team_a: 0, 'total': 1})
            vs_key = tuple(sorted([team_a, venue]))
            vs_venue = self.venue_stats.get(vs_key, {team_a: 0, 'total': 1})
            fs_a = self.form_stats.get(team_a, [])
            fs_b = self.form_stats.get(team_b, [])

            w_a = ts_a[0] / ts_a[1]
            w_b = ts_b[0] / ts_b[1]
            h2h_a = h2h.get(team_a, 0) / h2h['total']
            v_a = vs_venue.get(team_a, 0) / vs_venue['total']
            r_a = np.mean(fs_a[-5:]) if fs_a else 0.5
            r_b = np.mean(fs_b[-5:]) if fs_b else 0.5
            m_a = self.get_momentum(team_a)
            m_b = self.get_momentum(team_b)

            streak_a = 0
            for w in reversed(fs_a[-10:]):
                if w == 1: streak_a += 1
                else: break
            streak_b = 0
            for w in reversed(fs_b[-10:]):
                if w == 1: streak_b += 1
                else: break

            features = [[
                ta_enc, tb_enc, v_enc, w_a, w_b, h2h_a, v_a,
                r_a, r_b, m_a, m_b, streak_a, streak_b,
                w_a - w_b, r_a - r_b, h2h_a - 0.5,
                m_a - m_b, streak_a - streak_b
            ]]

            features_scaled = self.scaler.transform(features)

            winner_prob = (
                0.3 * self.models['rf'].predict_proba(features_scaled)[0] +
                0.3 * self.models['gb'].predict_proba(features_scaled)[0] +
                0.25 * self.models['et'].predict_proba(features_scaled)[0] +
                0.15 * self.models['lr'].predict_proba(features_scaled)[0]
            )

            margin_prob = self.margin_model.predict_proba(features_scaled)[0]

            probs = [
                winner_prob[0] * margin_prob[1],
                winner_prob[0] * margin_prob[0],
                winner_prob[1] * margin_prob[1],
                winner_prob[1] * margin_prob[0]
            ]

            total = sum(probs)
            probs = [p / total for p in probs]

            return dict(zip(self.classes, probs))

        except Exception as e:
            print(f"[MatchPredictor] Error: {e}")
            return {c: 0.25 for c in self.classes}

    def get_team_stats(self, team):
        if team not in self.team_stats:
            return {'wins': 0, 'total': 0, 'win_rate': 0.5, 'recent': []}
        stats = self.team_stats[team]
        return {
            'wins': stats[0],
            'total': stats[1],
            'win_rate': stats[0] / stats[1] if stats[1] > 0 else 0.5,
            'recent': self.form_stats.get(team, [])[-5:]
        }

    def get_h2h_record(self, team_a, team_b):
        h2h_key = tuple(sorted([team_a, team_b]))
        h2h = self.h2h_stats.get(h2h_key, {team_a: 0, team_b: 0, 'total': 0})
        return {
            'total': h2h['total'],
            team_a: h2h.get(team_a, 0),
            team_b: h2h.get(team_b, 0)
        }


# ============================================================================
# INCREMENTAL SCORER - For Live Match Updates
# ============================================================================

class IncrementalScorer:
    """Model that improves prediction confidence as innings progresses"""

    def __init__(self):
        self.team_le = LabelEncoder()
        self.model = None
        self.scaler = StandardScaler()
        self.classes = ['A_big', 'A_small', 'B_big', 'B_small']
        self.is_trained = False

    def calculate_confidence(self, overs_bowled):
        """Confidence increases with overs bowled"""
        if overs_bowled >= 20:
            return 0.95
        elif overs_bowled >= 18:
            return 0.90
        elif overs_bowled >= 15:
            return 0.80
        elif overs_bowled >= 10:
            return 0.70
        elif overs_bowled >= 6:
            return 0.55
        else:
            return 0.35

    def predict_from_live_state(self, live_state):
        """Predict based on current innings state"""
        overs = live_state.get('over', 0)
        runs = live_state.get('runs', 0)
        run_rate = live_state.get('current_run_rate', 8.0)

        confidence = self.calculate_confidence(overs)
        projected_total = run_rate * 20

        return {
            'confidence': confidence,
            'projected_total': round(projected_total, 1),
            'method': 'incremental_scorer'
        }


# ============================================================================
# LIVE MATCH API CLIENT
# ============================================================================

class LiveMatchClient:
    """Client for fetching live match data and making predictions"""

    def __init__(self, predictor):
        self.predictor = predictor
        self.scorer = IncrementalScorer()
        self.base_url = "https://www.cricbuzz.com/api/cricket-match/live"

    def fetch_live_matches(self):
        """Fetch current live matches from Cricbuzz"""
        import requests
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[LIVE] API Error: {e}")
        return None

    def parse_live_match(self, data):
        """Parse live match data to extract current match info"""
        if not data or 'matches' not in data:
            return None

        for match in data.get('matches', []):
            status = match.get('status', '').lower()
            if 'in progress' in status or 'live' in status:
                return {
                    'id': match.get('id'),
                    'status': status,
                    'team_1_name': match.get('team_1', {}).get('name', 'Unknown'),
                    'team_1_score': match.get('team_1', {}).get('score', '0/0'),
                    'team_1_overs': match.get('team_1', {}).get('overs', '0'),
                    'team_2_name': match.get('team_2', {}).get('name', 'Unknown'),
                    'team_2_score': match.get('team_2', {}).get('score', '0/0'),
                    'team_2_overs': match.get('team_2', {}).get('overs', '0'),
                    'venue': match.get('venue', 'Unknown'),
                    'series': match.get('series', 'IPL 2026'),
                    'innings': match.get('innings', 1),
                }
        return None

    def predict_live_innings(self, live_match):
        """Make prediction for live match with incremental scoring"""
        team_1 = live_match.get('team_1_name', 'Team A')
        team_2 = live_match.get('team_2_name', 'Team B')
        venue = live_match.get('venue', 'Unknown')

        # Parse score
        score_1 = live_match.get('team_1_score', '0/0')
        overs_1 = live_match.get('team_1_overs', '0')
        score_2 = live_match.get('team_2_score', '0/0')
        overs_2 = live_match.get('team_2_overs', '0')

        def parse_score(score_str):
            if not score_str or '/' not in score_str:
                return 0, 0
            parts = score_str.split('/')
            return int(parts[0]) if parts[0] else 0, int(parts[1]) if len(parts) > 1 else 0

        def parse_overs(overs_str):
            if not overs_str:
                return 0.0
            try:
                return float(overs_str)
            except:
                return 0.0

        runs_1, wickets_1 = parse_score(score_1)
        overs_1 = parse_overs(overs_1)
        runs_2, wickets_2 = parse_score(score_2)
        overs_2 = parse_overs(overs_2)

        innings = live_match.get('innings', 1)

        # Calculate overs and confidence
        if innings == 1:
            overs_bowled = overs_1
            current_runs = runs_1
            current_wickets = wickets_1
        else:
            overs_bowled = overs_2
            current_runs = runs_2
            current_wickets = wickets_2

        confidence = self.scorer.calculate_confidence(overs_bowled)
        run_rate = (current_runs / overs_bowled * 6) if overs_bowled > 0 else 0

        # Get base predictions
        probs = self.predictor.predict_match(team_1, team_2, venue)

        # Adjust based on current innings
        if innings == 1:
            projected_total = current_runs + ((20 - overs_bowled) * (run_rate + 2))
            if projected_total > 180:
                adjustment = 0.15
            elif projected_total > 160:
                adjustment = 0.05
            else:
                adjustment = -0.05

            base_win_prob = probs.get('A_big', 0.25) + probs.get('A_small', 0.25)
            a_total = base_win_prob + adjustment
            b_total = 1 - base_win_prob - adjustment
            probs['A_big'] = a_total * 0.6
            probs['A_small'] = a_total * 0.4
            probs['B_big'] = b_total * 0.6
            probs['B_small'] = b_total * 0.4
        else:
            target = runs_1
            required = target - current_runs + 1
            balls_left = int((20 - overs_bowled) * 6)
            required_rr = (required * 6 / balls_left) if balls_left > 0 else 999

            if required_rr > 15:
                adjustment = 0.20
            elif required_rr > 12:
                adjustment = 0.10
            elif required_rr > 10:
                adjustment = 0.0
            else:
                adjustment = -0.15

            base_win_prob = probs.get('B_big', 0.25) + probs.get('B_small', 0.25)
            new_b_prob = max(0.1, min(0.9, base_win_prob + adjustment))
            new_a_prob = 1 - new_b_prob

            probs['A_big'] = new_a_prob * 0.5
            probs['A_small'] = new_a_prob * 0.5
            probs['B_big'] = new_b_prob * 0.6
            probs['B_small'] = new_b_prob * 0.4

        # Normalize
        total = sum(probs.values())
        probs = {k: v/total for k, v in probs.items()}

        return {
            'match_info': {
                'team_1': team_1,
                'team_2': team_2,
                'venue': venue,
                'innings': innings
            },
            'live_state': {
                'team_1_score': score_1,
                'team_1_overs': overs_1,
                'team_2_score': score_2,
                'team_2_overs': overs_2,
                'run_rate': round(run_rate, 2)
            },
            'predictions': {
                'A_big': round(probs.get('A_big', 0) * 100, 1),
                'A_small': round(probs.get('A_small', 0) * 100, 1),
                'B_big': round(probs.get('B_big', 0) * 100, 1),
                'B_small': round(probs.get('B_small', 0) * 100, 1)
            },
            'most_likely': max(probs, key=probs.get),
            'confidence': round(confidence * 100, 1),
            'prediction_quality': 'improving' if overs_bowled > 10 else 'developing',
            'projected_total': round(run_rate * 20, 1)
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__" or True:
    # This runs in Kaggle notebook context
    print("=" * 70)
    print("🏏 IPL MATCH PREDICTOR - KAGGLE READY")
    print("=" * 70)

    # Load data path (Kaggle compatible)
    DATA_PATH = "/kaggle/input/ipl-match-data/"

    # Check if running in Kaggle
    if os.path.exists("/kaggle/input"):
        print("[KAGGLE] Running in Kaggle environment")
        SUMMARY_CSV = "/kaggle/input/ipl-match-data/match_summary.csv"
    else:
        print("[LOCAL] Running in local environment")
        SUMMARY_CSV = "backend/data/match_summary.csv"

    # Initialize and train
    print("\n[1] Training Match Predictor...")
    predictor = MatchPredictor()
    predictor.train(SUMMARY_CSV)

    print("\n[2] Initializing Live Match Client...")
    client = LiveMatchClient(predictor)

    # Test predictions
    print("\n" + "=" * 70)
    print("SAMPLE PREDICTIONS")
    print("=" * 70)

    test_matches = [
        ('Sunrisers Hyderabad', 'Kolkata Knight Riders',
         'Rajiv Gandhi International Stadium, Uppal, Hyderabad'),
        ('Gujarat Titans', 'Punjab Kings',
         'Narendra Modi Stadium, Ahmedabad'),
        ('Mumbai Indians', 'Lucknow Super Giants',
         'Wankhede Stadium, Mumbai'),
    ]

    for team_a, team_b, venue in test_matches:
        print(f"\n📊 {team_a} vs {team_b}")
        print(f"   Venue: {venue}")
        probs = predictor.predict_match(team_a, team_b, venue)
        print("   Predictions:")
        for k, v in sorted(probs.items(), key=lambda x: -x[1]):
            print(f"      {k}: {v*100:.1f}%")
        stats_a = predictor.get_team_stats(team_a)
        stats_b = predictor.get_team_stats(team_b)
        print(f"   {team_a} Win Rate: {stats_a['win_rate']*100:.1f}%")
        print(f"   {team_b} Win Rate: {stats_b['win_rate']*100:.1f}%")

    print("\n" + "=" * 70)
    print("✅ Model ready for predictions!")
    print("=" * 70)