import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class IPLPredictor:
    def __init__(self, data_path):
        self.data_path = data_path
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        
    def prepare_data(self):
        # In a real scenario, this would load the CSV. 
        # For demonstration, we'll create a dummy dataset reflecting the requirements
        try:
            df = pd.read_csv(self.data_path)
            # Filter for PBKS vs MI
            df = df[((df['batting_team'] == 'Punjab Kings') & (df['bowling_team'] == 'Mumbai Indians')) | 
                    ((df['batting_team'] == 'Mumbai Indians') & (df['bowling_team'] == 'Punjab Kings'))]
        except FileNotFoundError:
            print("CSV not found, generating synthetic training data for PBKS vs MI...")
            df = self._generate_synthetic_data()

        # Weighting for Dharamshala
        dharamshala_mask = df['venue'].str.contains('Dharamshala', case=False, na=False)
        # We use sample weights during training: higher weight for Dharamshala
        sample_weights = np.where(dharamshala_mask, 3.0, 1.0)
        
        # Features: current run rate, bowler economy, batsman strike rate, innings phase
        X = df[['current_run_rate', 'bowler_economy', 'batsman_strike_rate', 'is_powerplay', 'is_death']]
        
        # Clean up outcomes (Standardize to Dot, 1, 2, 3, 4, 6, Wicket)
        def map_outcome(val):
            val = str(val)
            if val in ['Dot', '0', '0.0']: return 'Dot'
            if val in ['Wicket', 'w', '-1']: return 'Wicket'
            if val in ['1', '2', '3', '4', '6']: return val
            if '1' in val: return '1'
            if '2' in val: return '2'
            if '3' in val: return '3'
            if '4' in val: return '4'
            if '6' in val: return '6'
            return 'Dot' # Default to Dot for outliers like '7' or extras
            
        y = df['outcome'].apply(map_outcome)
        
        return X, y, sample_weights

    def train(self):
        X, y, weights = self.prepare_data()
        self.model.fit(X, y, sample_weight=weights)
        print("Model trained successfully.")

    def predict_next_ball(self, match_state):
        """
        match_state: dict containing:
        - current_run_rate
        - bowler_economy
        - batsman_strike_rate
        - is_powerplay (1 or 0)
        - is_death (1 or 0)
        - delivery_type (optional, from vision pipeline)
        """
        features = [[
            match_state.get('current_run_rate', 8.0),
            match_state.get('bowler_economy', 7.5),
            match_state.get('batsman_strike_rate', 130.0),
            match_state.get('is_powerplay', 0),
            match_state.get('is_death', 0)
        ]]
        
        probs = self.model.predict_proba(features)[0]
        classes = self.model.classes_
        
        prediction = {str(cls): prob for cls, prob in zip(classes, probs)}
        return prediction

    def _generate_synthetic_data(self):
        n_samples = 1000
        np.random.seed(42)
        data = {
            'batting_team': np.random.choice(['Punjab Kings', 'Mumbai Indians'], n_samples),
            'bowling_team': np.random.choice(['Punjab Kings', 'Mumbai Indians'], n_samples),
            'venue': np.random.choice(['Wankhede', 'Mohali', 'Dharamshala'], n_samples, p=[0.4, 0.4, 0.2]),
            'current_run_rate': np.random.uniform(6.0, 12.0, n_samples),
            'bowler_economy': np.random.uniform(5.0, 11.0, n_samples),
            'batsman_strike_rate': np.random.uniform(100.0, 180.0, n_samples),
            'is_powerplay': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'is_death': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'outcome': np.random.choice(['Dot', '1', '2', '4', '6', 'Wicket'], n_samples)
        }
        return pd.DataFrame(data)

if __name__ == "__main__":
    predictor = IPLPredictor(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\ipl_deliveries.csv")
    predictor.train()
    
    sample_state = {
        'current_run_rate': 9.5,
        'bowler_economy': 8.2,
        'batsman_strike_rate': 145.0,
        'is_powerplay': 0,
        'is_death': 1,
        'delivery_type': 'yorker'
    }
    
    print("Prediction for next ball:", predictor.predict_next_ball(sample_state))
