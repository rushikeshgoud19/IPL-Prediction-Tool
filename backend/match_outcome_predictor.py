import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

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

    def get_momentum(self, team):
        if team not in self.form_stats or len(self.form_stats[team]) < 3:
            return 0
        return sum(self.form_stats[team][-3:])

    def prepare_features(self, df):
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # Encode
        all_teams = pd.concat([df['team_a'], df['team_b']]).unique()
        self.team_le.fit(all_teams)
        self.venue_le.fit(df['venue'].unique())

        df['team_a_enc'] = self.team_le.transform(df['team_a'])
        df['team_b_enc'] = self.team_le.transform(df['team_b'])
        df['venue_enc'] = self.venue_le.transform(df['venue'])

        # Rolling features
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

            # Update after match
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
        print("[MatchPredictor] Loading %d matches..." % len(pd.read_csv(summary_csv)))

        df = pd.read_csv(summary_csv)
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

        # Train ensemble of models
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

        print("[MatchPredictor] Training ensemble (4 models)...")
        rf.fit(X_scaled, self.y_winner)
        gb.fit(X_scaled, self.y_winner)
        et.fit(X_scaled, self.y_winner)
        lr.fit(X_scaled, self.y_winner)

        self.models = {'rf': rf, 'gb': gb, 'et': et, 'lr': lr}

        # Margin model
        self.margin_model = GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
        self.margin_model.fit(X_scaled, self.y_margin)

        print("[MatchPredictor] Training complete!")

    def predict_match(self, team_a, team_b, venue,
                     wr_a=None, wr_b=None, h2h_wr_a=None,
                     venue_wr_a=None, recent_form_a=None, recent_form_b=None):
        if not self.models:
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

            w_a = wr_a if wr_a else ts_a[0] / ts_a[1]
            w_b = wr_b if wr_b else ts_b[0] / ts_b[1]
            h2h_a = h2h_wr_a if h2h_wr_a else h2h.get(team_a, 0) / h2h['total']
            v_a = venue_wr_a if venue_wr_a else vs_venue.get(team_a, 0) / vs_venue['total']
            r_a = recent_form_a if recent_form_a else np.mean(fs_a[-5:]) if fs_a else 0.5
            r_b = recent_form_b if recent_form_b else np.mean(fs_b[-5:]) if fs_b else 0.5
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

            # Ensemble predictions
            winner_prob = (
                0.3 * self.models['rf'].predict_proba(features_scaled)[0] +
                0.3 * self.models['gb'].predict_proba(features_scaled)[0] +
                0.25 * self.models['et'].predict_proba(features_scaled)[0] +
                0.15 * self.models['lr'].predict_proba(features_scaled)[0]
            )

            margin_prob = self.margin_model.predict_proba(features_scaled)[0]

            # Combine to 4-class
            probs = [
                winner_prob[0] * margin_prob[1],  # A_big
                winner_prob[0] * margin_prob[0],  # A_small
                winner_prob[1] * margin_prob[1],  # B_big
                winner_prob[1] * margin_prob[0]   # B_small
            ]

            total = sum(probs)
            probs = [p / total for p in probs]

            return dict(zip(self.classes, probs))

        except Exception as e:
            print("[MatchPredictor] Error: %s" % e)
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

if __name__ == "__main__":
    predictor = MatchPredictor()
    predictor.train(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv")

    targets = [
        ('Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Rajiv Gandhi International Stadium, Uppal, Hyderabad'),
        ('Gujarat Titans', 'Punjab Kings', 'Narendra Modi Stadium, Ahmedabad'),
        ('Mumbai Indians', 'Lucknow Super Giants', 'Wankhede Stadium, Mumbai'),
    ]

    print("\n[PREDICTIONS]")
    for team_a, team_b, venue in targets:
        print("\n%s vs %s:" % (team_a, team_b))
        probs = predictor.predict_match(team_a, team_b, venue)
        for k, v in sorted(probs.items(), key=lambda x: -x[1]):
            print("  %s: %.1f%%" % (k, v * 100))