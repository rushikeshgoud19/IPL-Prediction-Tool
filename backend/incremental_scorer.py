import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')

class IncrementalScorer:
    """
    Model that improves prediction confidence as innings progresses.
    Uses current score, run rate, and momentum to update match outcome predictions.
    """

    def __init__(self):
        self.team_le = LabelEncoder()
        self.model = None
        self.scaler = StandardScaler()
        self.classes = ['A_big', 'A_small', 'B_big', 'B_small']
        self.baseline_predictions = {}

    def train(self, data_path):
        """
        Train model on historical innings data to learn score progression patterns.
        """
        print("[IncrementalScorer] Training on historical innings data...")

        try:
            df = pd.read_csv(data_path)
            print(f"[IncrementalScorer] Loaded {len(df)} deliveries")
        except FileNotFoundError:
            print("[IncrementalScorer] Data file not found. Using baseline model.")
            return

        # Build innings-level dataset from ball-by-ball data
        innings_data = self._build_innings_features(df)

        if len(innings_data) < 50:
            print("[IncrementalScorer] Not enough innings data, using baseline model.")
            return

        # Prepare features
        X = innings_data[['over', 'runs', 'wickets', 'run_rate', 'projected_total', 'run_diff']].values
        y_winner = innings_data['winner'].values  # 0 = team A won, 1 = team B won

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Train model to predict winner based on innings progression
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X_scaled, y_winner)

        print("[IncrementalScorer] Training complete!")

    def _build_innings_features(self, df):
        """Extract innings-level features from ball-by-ball data"""
        innings_list = []

        for (match_id, innings), group in df.groupby(['match_id', 'innings']):
            if len(group) < 6:  # Skip incomplete innings
                continue

            group = group.sort_values('ball')

            # Get final result
            winner = group['winner'].iloc[0] if 'winner' in group.columns else None
            if pd.isna(winner):
                continue

            # Features at different over milestones
            for over_milestone in [6, 10, 15, 18]:
                over_data = group[group['ball'] <= over_milestone]
                if len(over_data) < 3:
                    continue

                runs = over_data['runs_off_bat'].sum()
                wickets = over_data['wickets'].sum() if 'wickets' in over_data.columns else 0
                balls = len(over_data)
                run_rate = (runs / balls) * 6 if balls > 0 else 0
                projected_total = run_rate * 20

                # Compare to typical scores at this stage
                run_diff = runs - (over_milestone * 8)  # vs expected 8 run rate

                innings_list.append({
                    'match_id': match_id,
                    'innings': innings,
                    'over': over_milestone,
                    'runs': runs,
                    'wickets': wickets,
                    'run_rate': run_rate,
                    'projected_total': projected_total,
                    'run_diff': run_diff,
                    'winner': 0 if winner == 'A' else 1
                })

        return pd.DataFrame(innings_list)

    def calculate_confidence(self, overs_bowled):
        """
        Calculate prediction confidence based on overs bowled.
        Returns value between 0.3 (start) and 0.95 (end of innings).
        """
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
        """
        Predict next ball outcome from current live state.
        Also calculates match outcome confidence.
        """
        if not self.model:
            return {
                'ball_probs': {},
                'confidence': 0.5,
                'method': 'baseline'
            }

        overs = live_state.get('over', 0)
        runs = live_state.get('runs', 0)
        wickets = live_state.get('wickets', 0)
        run_rate = live_state.get('current_run_rate', 8.0)

        # Projected total based on current run rate
        projected_total = run_rate * 20

        # Compare to baseline (8 run rate = 160 total)
        run_diff = runs - (overs * 8) if overs > 0 else 0

        try:
            features = [[overs, runs, wickets, run_rate, projected_total, run_diff]]
            features_scaled = self.scaler.transform(features)

            # Get win probability
            probs = self.model.predict_proba(features_scaled)[0]
            confidence = self.calculate_confidence(overs)

            return {
                'team_a_win_prob': round(probs[0], 3),
                'team_b_win_prob': round(probs[1], 3),
                'confidence': confidence,
                'projected_total': round(projected_total, 1),
                'method': 'incremental_model'
            }
        except Exception as e:
            print(f"[IncrementalScorer] Prediction error: {e}")
            return {
                'confidence': self.calculate_confidence(overs),
                'method': 'fallback'
            }

    def update_prediction_with_score(self, base_probs, live_state):
        """
        Update base match probabilities based on current innings score.
        Returns adjusted probabilities with confidence level.
        """
        overs = live_state.get('over', 0)
        runs = live_state.get('runs', 0)
        target = live_state.get('target', None)
        innings = live_state.get('innings', 1)

        # Calculate current confidence
        confidence = self.calculate_confidence(overs)

        if innings == 1:
            # First innings - adjust based on projected total
            current_rr = (runs / overs * 6) if overs > 0 else 0
            projected_total = current_rr * 20

            # Adjust A team win probability based on projected score
            if projected_total >= 200:
                adjustment = 0.25
            elif projected_total >= 180:
                adjustment = 0.15
            elif projected_total >= 160:
                adjustment = 0.05
            elif projected_total >= 140:
                adjustment = -0.05
            else:
                adjustment = -0.15

            # Blend base predictions with score-based adjustment
            a_prob = (base_probs.get('A_big', 0) + base_probs.get('A_small', 0)) + adjustment * (1 - confidence)
            a_prob = max(0.1, min(0.9, a_prob))
            b_prob = 1 - a_prob

            # Re-normalize to 4 classes
            return {
                'A_big': a_prob * 0.55,
                'A_small': a_prob * 0.45,
                'B_big': b_prob * 0.55,
                'B_small': b_prob * 0.45,
                'confidence': confidence,
                'projected_total': round(projected_total, 1),
                'adjustment_reason': 'first_innings_projection'
            }
        else:
            # Second innings - chase calculation
            if target:
                required = target - runs + 1
                balls_left = (20 - overs) * 6
                required_rr = (required * 6 / balls_left) if balls_left > 0 else 999

                # Higher required RR = harder chase = team 1 more likely to win
                if required_rr >= 18:
                    adjustment = 0.30
                elif required_rr >= 15:
                    adjustment = 0.15
                elif required_rr >= 12:
                    adjustment = 0.05
                elif required_rr >= 10:
                    adjustment = -0.05
                else:
                    adjustment = -0.20

                b_prob = (base_probs.get('B_big', 0) + base_probs.get('B_small', 0)) + adjustment * (1 - confidence)
                b_prob = max(0.1, min(0.9, b_prob))
                a_prob = 1 - b_prob

                return {
                    'A_big': a_prob * 0.55,
                    'A_small': a_prob * 0.45,
                    'B_big': b_prob * 0.55,
                    'B_small': b_prob * 0.45,
                    'confidence': confidence,
                    'required_rr': round(required_rr, 2),
                    'balls_remaining': balls_left,
                    'adjustment_reason': 'chase_calculation'
                }

        # Fallback - return base with adjusted confidence
        return {
            **{k: v for k, v in base_probs.items()},
            'confidence': confidence,
            'adjustment_reason': 'overs_progress'
        }

if __name__ == "__main__":
    scorer = IncrementalScorer()
    scorer.train(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\ipl_deliveries.csv")

    # Test cases
    print("\n[INCREMENTAL SCORER TESTS]")

    test_states = [
        {'over': 5, 'runs': 40, 'wickets': 1, 'current_run_rate': 8.0, 'innings': 1},
        {'over': 10, 'runs': 85, 'wickets': 2, 'current_run_rate': 8.5, 'innings': 1},
        {'over': 15, 'runs': 140, 'wickets': 4, 'current_run_rate': 9.3, 'innings': 1},
        {'over': 18, 'runs': 175, 'wickets': 5, 'current_run_rate': 9.7, 'innings': 1},
    ]

    for state in test_states:
        result = scorer.predict_from_live_state(state)
        print(f"\nOver {state['over']}: {state['runs']}/{state['wickets']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Projected Total: {result.get('projected_total', 'N/A')}")