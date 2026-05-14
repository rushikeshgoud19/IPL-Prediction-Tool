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

# Example of how the state will look when live:
mock_live_state = {
    "match": "PBKS vs MI",
    "venue": "Dharamshala",
    "status": "LIVE",
    "batting_team": "PBKS",
    "bowling_team": "MI",
    "over": 18.4,
    "runs": 178,
    "wickets": 4,
    "current_run_rate": 9.5,
    "batsman_strike_rate": 145.0,
    "bowler_economy": 8.2,
    "is_powerplay": 0,
    "is_death": 1,
    "delivery_type": "Yorker",
    "last_prediction": {
        "outcome": "1",
        "probs": {"Dot": 10, "1": 45, "2": 20, "4": 15, "6": 5, "Wicket": 5},
        "historical_context": "At this venue in the death overs (16-20), MI bowlers pitch 42% Yorkers. Given PBKS's current run rate of 9.5, a single is the highest probability."
    },
    "recent_overs": [
        ["1", "Dot", "4", "1", "Wicket", "1"],
        ["6", "2", "1", "Dot", "4", "1"]
    ]
}

# Simulation removed. The dashboard will now wait for actual data or can be toggled to show the mock state.
@app.route('/api/toggle-demo', methods=['POST'])
def toggle_demo():
    global live_match_state
    if live_match_state["status"] == "AWAITING TOSS":
        live_match_state = mock_live_state
    else:
        # Reset to pending
        live_match_state = {
            "match": "PBKS vs MI", "venue": "Dharamshala", "status": "AWAITING TOSS", "over": 0.0, "runs": 0, "wickets": 0,
            "current_run_rate": 0.0, "last_prediction": {"outcome": "STANDBY", "probs": {}, "historical_context": "Match hasn't started yet."},
            "recent_overs": []
        }
    return jsonify({"success": True})

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
            "predictions": {k: round(v * 100, 2) for k, v in probs.items()}
        })
    return jsonify(results)

if __name__ == '__main__':
    print("Dashboard Backend Started. API running on http://localhost:5000/api/live")
    app.run(port=5000, debug=False, use_reloader=False)
