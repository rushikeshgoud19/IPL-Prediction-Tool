import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import log_loss, classification_report
import warnings
warnings.filterwarnings('ignore')

class BallPredictor:
    """Predicts ball-by-ball outcomes (Dot, 1, 2, 3, 4, 6, Wicket)"""
    def __init__(self, data_path):
        self.data_path = data_path
        self.team_le = LabelEncoder()
        self.bowler_le = LabelEncoder()
        self.batsman_le = LabelEncoder()
        self.model = None
        self.scaler = StandardScaler()
        self.outcome_classes = ['Dot', '1', '2', '3', '4', '6', 'Wicket']

    def prepare_data(self):
        """Load and prepare data for ball-by-ball prediction"""
        try:
            df = pd.read_csv(self.data_path)
            print(f"Loaded {len(df)} deliveries")
        except FileNotFoundError:
            print("❌ Data file not found. Run data_pipeline.py first.")
            return None, None, None

        # Create binary features for special situations
        df['is_powerplay'] = df['ball'].apply(lambda x: 1 if float(x) < 6 else 0)
        df['is_death'] = df['ball'].apply(lambda x: 1 if float(x) >= 15 else 0)
        df['is_yorker_ball'] = ((df['ball'] % 1).astype(float) > 0.85).astype(int)

        # Clean outcome
        def clean_outcome(row):
            if pd.notna(row.get('wicket_type')):
                return 'Wicket'
            runs = row.get('runs_off_bat', 0)
            if pd.isna(runs):
                return 'Dot'
            runs = int(runs)
            if runs == 0:
                return 'Dot'
            return str(runs)

        df['outcome'] = df.apply(clean_outcome, axis=1)

        # Encode categorical variables
        try:
            all_teams = pd.concat([df['batting_team'], df['bowling_team']]).unique()
            self.team_le.fit(all_teams)

            df['batting_team_enc'] = self.team_le.transform(df['batting_team'])
            df['bowling_team_enc'] = self.team_le.transform(df['bowling_team'])

            # Fit batsman and bowler encoders
            all_batsmen = df['striker'].dropna().unique()
            all_bowlers = df['bowler'].dropna().unique()
            self.batsman_le.fit(list(all_batsmen) + ['UNKNOWN'])
            self.bowler_le.fit(list(all_bowlers) + ['UNKNOWN'])

            df['striker_enc'] = df['striker'].apply(
                lambda x: self.batsman_le.transform([x])[0] if x in self.batsman_le.classes_ else 0
            )
            df['bowler_enc'] = df['bowler'].apply(
                lambda x: self.bowler_le.transform([x])[0] if x in self.bowler_le.classes_ else 0
            )
        except Exception as e:
            print(f"⚠️ Encoding error: {e}")

        # Feature engineering
        df['runs_diff'] = df['current_run_rate'] - df['bowler_economy']
        df['sr_economy_ratio'] = df['batsman_strike_rate'] / (df['bowler_economy'] + 0.1)

        # Handle infinity values
        df = df.replace([np.inf, -np.inf], 0)

        return df

    def train(self):
        """Train the ball-by-ball prediction model"""
        print("=" * 60)
        print("BALL-BY-BALL PREDICTOR - TRAINING")
        print("=" * 60)

        df = self.prepare_data()
        if df is None:
            return False

        # Features
        feature_cols = [
            'batting_team_enc', 'bowling_team_enc',
            'current_run_rate', 'bowler_economy', 'batsman_strike_rate',
            'is_powerplay', 'is_death', 'is_yorker_ball',
            'runs_diff', 'sr_economy_ratio'
        ]

        # Check for missing columns
        missing_cols = [c for c in feature_cols if c not in df.columns]
        if missing_cols:
            print(f"Missing columns: {missing_cols}")
            # Use only available columns
            feature_cols = [c for c in feature_cols if c in df.columns]

        X = df[feature_cols].fillna(0)
        y = df['outcome']

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train/val split
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        print(f"\nTraining samples: {len(X_train)}")
        print(f"Validation samples: {len(X_val)}")

        # Train Gradient Boosting for better accuracy
        print("\n🔄 Training Gradient Boosting model...")
        base_model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        )

        # Calibrate for probability output
        self.model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
        self.model.fit(X_train, y_train)

        # Validation
        print("\n" + "=" * 60)
        print("BALL PREDICTOR VALIDATION")
        print("=" * 60)

        val_preds = self.model.predict(X_val)
        val_acc = (val_preds == y_val).mean()
        print(f"Validation Accuracy: {val_acc:.4f}")

        val_probs = self.model.predict_proba(X_val)
        ll = log_loss(y_val, val_probs, labels=self.outcome_classes)
        print(f"Log Loss: {ll:.4f}")

        # Cross-validation
        cv_scores = cross_val_score(base_model, X_scaled, y, cv=5, scoring='accuracy')
        print(f"5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Per-class accuracy
        print("\nPer-Class Performance:")
        for outcome in self.outcome_classes:
            mask = y_val == outcome
            if mask.sum() > 0:
                acc = (val_preds[mask] == outcome).mean()
                print(f"  {outcome}: {acc:.4f} ({mask.sum()} samples)")

        print("\n✅ Ball predictor trained successfully!")
        return True

    def predict_next_ball(self, match_state):
        """
        Predict next ball outcome.
        match_state: dict with:
        - current_run_rate
        - bowler_economy
        - batsman_strike_rate
        - is_powerplay (0/1)
        - is_death (0/1)
        - batting_team
        - bowling_team
        - bowler (optional)
        - striker (optional)
        """
        if self.model is None:
            return {o: 1/len(self.outcome_classes) for o in self.outcome_classes}

        try:
            # Encode teams
            if match_state.get('batting_team') in self.team_le.classes_:
                bat_enc = self.team_le.transform([match_state['batting_team']])[0]
            else:
                bat_enc = 0

            if match_state.get('bowling_team') in self.team_le.classes_:
                bowl_enc = self.team_le.transform([match_state['bowling_team']])[0]
            else:
                bowl_enc = 0

            # Calculate derived features
            crr = match_state.get('current_run_rate', 8.0)
            be = match_state.get('bowler_economy', 8.0)
            bsr = match_state.get('batsman_strike_rate', 130.0)
            runs_diff = crr - be
            sr_eco_ratio = bsr / (be + 0.1)

            features = [[
                bat_enc, bowl_enc,
                crr, be, bsr,
                match_state.get('is_powerplay', 0),
                match_state.get('is_death', 0),
                0,  # is_yorker_ball
                runs_diff, sr_eco_ratio
            ]]

            features_scaled = self.scaler.transform(features)
            probs = self.model.predict_proba(features_scaled)[0]

            return {str(cls): float(prob) for cls, prob in zip(self.outcome_classes, probs)}

        except Exception as e:
            print(f"Ball prediction error: {e}")
            return {o: 1/len(self.outcome_classes) for o in self.outcome_classes}

# Alias for backwards compatibility
IPLPredictor = BallPredictor

if __name__ == "__main__":
    predictor = BallPredictor(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\ipl_deliveries.csv")
    success = predictor.train()

    if success:
        sample_state = {
            'current_run_rate': 9.5,
            'bowler_economy': 8.2,
            'batsman_strike_rate': 145.0,
            'is_powerplay': 0,
            'is_death': 1,
            'batting_team': 'Punjab Kings',
            'bowling_team': 'Mumbai Indians'
        }

        print("\n" + "=" * 60)
        print("SAMPLE PREDICTION")
        print("=" * 60)
        print(f"\nMatch State: {sample_state}")
        probs = predictor.predict_next_ball(sample_state)
        print("\nPredicted Outcomes:")
        for outcome, prob in sorted(probs.items(), key=lambda x: -x[1]):
            print(f"  {outcome}: {prob*100:.1f}%")