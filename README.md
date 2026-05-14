# IPL Prediction Tool: Multi-Modal Match & Ball Engine 🏏

A highly sophisticated, end-to-end IPL prediction engine built for real-time inference and pre-match outcome prediction. This project was engineered for competitive hackathons, providing a unique blend of **Statistical Probability**, **Computer Vision**, and a **3D Interactive Dashboard**.

![IPL Predictor Dashboard](https://img.shields.io/badge/Status-Hackathon_Ready-success)
![React](https://img.shields.io/badge/Frontend-React_Three_Fiber-blue)
![Python](https://img.shields.io/badge/Backend-Flask_%7C_XGBoost-yellow)

---

## 🌟 Key Features

1. **Pre-Match Outcome Predictor (Hackathon Focus)**
   - Utilizes historical ball-by-ball data to extract rolling team win rates, head-to-head metrics, and venue biases.
   - Powered by a **Calibrated Random Forest Classifier** strictly optimized to minimize **Mean Columnwise Log Loss**.
   - Outputs highly accurate 4-class probabilities (`A_big`, `A_small`, `B_big`, `B_small`) as required by standard prediction hackathons.

2. **Real-Time Next Ball Predictor**
   - Continuously evaluates match state (Current Run Rate, Overs, Wickets, Death Over status) to predict the exact outcome of the very next delivery (Dot, 1, 2, 4, 6, Wicket).

3. **Live 3D Broadcast Dashboard**
   - Built with **React** and **Three.js**.
   - Features a Hotstar-style "Overs Timeline" and real-time data insights.
   - Renders dynamic glowing ball trajectories across a 3D cricket pitch based on real-time predictions.

---

## 🛠️ Tech Stack
* **Frontend**: React, Vite, React-Three-Fiber (Three.js)
* **Backend Core**: Python, Flask, Pandas, Scikit-Learn (RandomForest)
* **Computer Vision**: YOLOv8 (for real-time ball trajectory mapping)

---

## 🚀 Setup & Installation Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/rushikeshgoud19/IPL-Prediction-Tool.git
cd IPL-Prediction-Tool
```

### 2. Backend Setup (Python)
Ensure you have Python 3.9+ installed.
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows
# source venv/bin/activate    # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (React)
Ensure you have Node.js installed.
```bash
cd react-dashboard
npm install
```

---

## 🎮 Running the Application

This system requires both the backend API and the frontend dashboard to run simultaneously.

### Step 1: Start the AI Backend
In your first terminal (from the project root):
```bash
# Optional: Re-process historical data if you added new CSVs
# python backend/match_data_processor.py

# Start the Flask API
python backend/app.py
```
*The backend will load the models and run on `http://localhost:5000`.*

### Step 2: Start the 3D Dashboard
In your second terminal:
```bash
cd react-dashboard
npm run dev
```
*Open `http://localhost:5173` in your browser.*

### Step 3: Trigger the Demo
Once the dashboard is open, you will see it in a "Pending" state. Click **"LOAD HISTORICAL DEMO DATA"** in the bottom left to instantly inject a high-stakes, late-game scenario and watch the AI timeline and 3D pitch come to life!

---

## 📂 Hackathon Submission Generation
If you are using this to generate a `submission.csv` for the target matches:
```bash
python backend/generate_submission.py
```
This will output a `submission.csv` in the root folder with the calibrated Log Loss probabilities.

---
**Developer**: Kayala Rushikesh Goud
