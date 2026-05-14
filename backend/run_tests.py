from prediction_core import IPLPredictor
import pandas as pd

def run_extreme_tests():
    predictor = IPLPredictor(r"backend/data/ipl_deliveries.csv")
    predictor.train()
    
    test_cases = [
        {
            "name": "High-Pressure Death Overs (Match Winning Ball?)",
            "state": {
                'current_run_rate': 14.5,
                'bowler_economy': 10.2,
                'batsman_strike_rate': 195.0,
                'is_powerplay': 0,
                'is_death': 1
            }
        },
        {
            "name": "Powerplay Masterclass (Early Aggression)",
            "state": {
                'current_run_rate': 11.2,
                'bowler_economy': 6.5,
                'batsman_strike_rate': 160.0,
                'is_powerplay': 1,
                'is_death': 0
            }
        },
        {
            "name": "Mid-Innings Stranglehold (Defensive Bowling)",
            "state": {
                'current_run_rate': 6.8,
                'bowler_economy': 5.2,
                'batsman_strike_rate': 110.0,
                'is_powerplay': 0,
                'is_death': 0
            }
        },
        {
            "name": "Tailender Struggle (High Wicket Probability)",
            "state": {
                'current_run_rate': 5.5,
                'bowler_economy': 9.8,
                'batsman_strike_rate': 85.0,
                'is_powerplay': 0,
                'is_death': 1
            }
        }
    ]
    
    print("\n" + "="*50)
    print("RUNNING CRAZY TEST CASES")
    print("="*50)
    
    for tc in test_cases:
        print(f"\nTEST: {tc['name']}")
        print(f"INPUT: {tc['state']}")
        pred = predictor.predict_next_ball(tc['state'])
        
        # Sort and show top 3
        sorted_pred = sorted(pred.items(), key=lambda x: x[1], reverse=True)[:3]
        print("TOP PREDICTIONS:")
        for outcome, prob in sorted_pred:
            print(f"  - {outcome}: {prob*100:.2f}%")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    run_extreme_tests()
