import requests
import time
from prediction_core import IPLPredictor

class LiveMatchClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url
        
        # Standard way to pass an API key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize and train our model
        self.predictor = IPLPredictor("data/ipl_deliveries.csv")
        self.predictor.train()

    def fetch_live_state(self):
        try:
            # Fetch the live match JSON from the hackathon API
            response = requests.get(self.api_url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                # Let's assume the API returns a 'match_state' dictionary
                return data.get('match_state', {})
            else:
                print(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

    def start_polling(self, interval_seconds=2):
        print(f"Connecting to live API with key ending in ...{self.api_key[-4:]}")
        last_ball_id = None
        
        while True:
            live_state = self.fetch_live_state()
            
            # Only run the prediction if the API gives us a new delivery
            if live_state and live_state.get('ball_id') != last_ball_id:
                prediction = self.predictor.predict_next_ball(live_state)
                
                print(f"\n--- NEW DELIVERY DETECTED ---")
                print(f"Live Stats -> RR: {live_state.get('current_run_rate')} | Phase: {live_state.get('is_death')}")
                print(f"Prediction -> {prediction}")
                
                # Here you could send this prediction to your 3D Frontend!
                
                last_ball_id = live_state.get('ball_id')
                
            time.sleep(interval_seconds)

if __name__ == "__main__":
    # Example Usage: Plug your Hackathon details in here!
    HACKATHON_API_KEY = "your_secret_api_key_here"
    HACKATHON_API_URL = "https://api.ipl-hackathon.com/v1/matches/pbks-mi/live"
    
    client = LiveMatchClient(HACKATHON_API_KEY, HACKATHON_API_URL)
    # client.start_polling()
