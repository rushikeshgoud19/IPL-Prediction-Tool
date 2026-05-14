from flask import Flask, jsonify
from flask_cors import CORS
from prediction_core import IPLPredictor
from match_outcome_predictor import MatchPredictor
import random
import threading
import time

app = Flask(__name__)
CORS(app)

# Initialize Predictor
try:
    predictor = IPLPredictor(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\ipl_deliveries.csv")
    predictor.train()
    
    # Initialize Match-Outcome Predictor (Hackathon Focus)
    match_predictor = MatchPredictor()
    match_predictor.train(r"c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv")
    
    print("Models ready for live and pre-match dashboard!")
except Exception as e:
    print(f"Model failed to load/train: {e}")
    predictor = None
    match_predictor = None

# Real Match State (Pending Live Feed)
live_match_state = {
    "match": "PBKS vs MI",
    "venue": "Dharamshala",
    "status": "AWAITING TOSS",
    "batting_team": "-",
    "bowling_team": "-",
    "over": 0.0,
    "runs": 0,
    "wickets": 0,
    "current_run_rate": 0.0,
    "batsman_strike_rate": 0.0,
    "bowler_economy": 0.0,
    "is_powerplay": 0,
    "is_death": 0,
    "delivery_type": "-",
    "last_prediction": {
        "outcome": "STANDBY",
        "probs": {"Dot": 0, "1": 0, "2": 0, "4": 0, "6": 0, "Wicket": 0},
        "historical_context": "Match hasn't started yet. Awaiting live data feed to calculate next ball probabilities."
    },
    "recent_overs": []
}

# Simulation routes removed to focus on real data and hackathon requirements.

@app.route('/api/live', methods=['GET'])
def get_live_state():
    return jsonify(live_match_state)

@app.route('/api/pre-match', methods=['GET'])
def get_pre_match():
    if not match_predictor:
        return jsonify({"error": "Match Predictor not initialized"}), 500
        
    targets = [
        {'team_a': 'Sunrisers Hyderabad', 'team_b': 'Kolkata Knight Riders', 'venue': 'Rajiv Gandhi International Stadium, Uppal, Hyderabad', 'label': 'SRH vs KKR'},
        {'team_a': 'Gujarat Titans', 'team_b': 'Punjab Kings', 'venue': 'Narendra Modi Stadium, Ahmedabad', 'label': 'GT vs PBKS'},
        {'team_a': 'Mumbai Indians', 'team_b': 'Lucknow Super Giants', 'venue': 'Wankhede Stadium, Mumbai', 'label': 'MI vs LSG'}
    ]
    
    results = []
    for t in targets:
        probs = match_predictor.predict_match(t['team_a'], t['team_b'], t['venue'])
        results.append({
            "match": t['label'],
            "team_a": t['team_a'],
            "team_b": t['team_b'],
            "predictions": {k: round(v * 100, 2) for k, v in probs.items()}
        })
    return jsonify(results)

if __name__ == '__main__':
    print("Dashboard Backend Started. API running on http://localhost:5000/api/live")
    app.run(port=5000, debug=False, use_reloader=False)
