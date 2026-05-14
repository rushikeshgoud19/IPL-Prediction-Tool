# Kaggle Upload Instructions for IPL Predictor

## Files to Upload

1. **`ipl_predictor.ipynb`** - Main Kaggle notebook (self-contained)
2. **`kaggle_api.py`** - Standalone Python version
3. **`kaggle_requirements.txt`** - Dependencies
4. **`backend/data/`** - Your training data (CSV files)

## Step-by-Step Upload Guide

### Step 1: Prepare Your Data on Kaggle

1. Go to [kaggle.com](https://kaggle.com)
2. Create a new Dataset or Notebook
3. Upload your CSV files to `/kaggle/input/ipl-match-data/`

### Step 2: Upload the Notebook

1. Go to Kaggle Notebooks
2. Click "New Notebook"
3. Delete the default cell
4. Copy the content from `ipl_predictor.ipynb` into your notebook
5. Save

### Step 3: Verify Data Paths

In the notebook, update the data path if needed:
```python
# Kaggle path
SUMMARY_CSV = '/kaggle/input/ipl-match-data/match_summary.csv'
DELIVERIES_CSV = '/kaggle/input/ipl-match-data/ipl_deliveries.csv'
```

### Step 4: Run the Notebook

1. Click "Run All"
2. The model will train and generate predictions
3. Download the `submission.csv` file

## Features

- **Match Outcome Prediction**: Predicts A_big, A_small, B_big, B_small probabilities
- **Live Match Integration**: Fetches real-time data from Cricbuzz API
- **Incremental Scoring**: Confidence improves as the match progresses
- **Toss Prediction**: Predicts toss winner before match starts

## API Endpoints (when running as API)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/current-match` | Current live match with real team names |
| `GET /api/toss` | Toss prediction (active when match starts) |
| `GET /api/live/innings-predict` | Live innings prediction |
| `GET /api/pre-match` | Pre-match predictions |

## Model Confidence by Overs

| Overs Bowled | Confidence |
|-------------|------------|
| 0-5 | 35-45% |
| 5-10 | 55-65% |
| 10-15 | 65-75% |
| 15-18 | 75-90% |
| 18-20 | 90-95% |
