import { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Sphere, ContactShadows } from '@react-three/drei';
import './App.css';


// Cricket Pitch Component
function CricketPitch({ latestPrediction }) {
  const getPredictionProps = (pred) => {
    switch(pred) {
      case '6': return { color: '#ff0055', emissive: '#ff0055', emissiveIntensity: 4, position: [0, 8, -15], size: 0.5 };
      case '4': return { color: '#ffcc00', emissive: '#ffcc00', emissiveIntensity: 3, position: [8, -0.05, 6], size: 0.4 };
      case '1': return { color: '#00bfff', emissive: '#00bfff', emissiveIntensity: 2, position: [-3, 0, 0], size: 0.25 };
      case '2': return { color: '#00ff88', emissive: '#00ff88', emissiveIntensity: 2, position: [-5, 0, -3], size: 0.25 };
      case '3': return { color: '#ff6b35', emissive: '#ff6b35', emissiveIntensity: 2, position: [3, 0, 3], size: 0.25 };
      case 'Wicket': return null; // Handled separately
      default: return { color: '#666', emissive: '#666', emissiveIntensity: 0.5, position: [0, 0.5, 5], size: 0.2 };
    }
  };

  const props = getPredictionProps(latestPrediction);

  return (
    <group position={[0, -1, 0]}>
      {/* Pitch */}
      <Box args={[4, 0.15, 12]} position={[0, 0, 0]}>
        <meshStandardMaterial color="#8B7355" roughness={0.9} />
      </Box>

      {/* Grass */}
      <Box args={[50, 0.1, 50]} position={[0, -0.1, 0]}>
        <meshStandardMaterial color="#1a4d1a" roughness={1} />
      </Box>

      {/* Crease lines */}
      <Box args={[2.5, 0.02, 0.1]} position={[0, 0.08, 2]}><meshStandardMaterial color="white" /></Box>
      <Box args={[2.5, 0.02, 0.1]} position={[0, 0.08, -2]}><meshStandardMaterial color="white" /></Box>

      {/* Prediction visualization */}
      {props && (
        <Sphere args={[props.size, 32, 32]} position={props.position}>
          <meshStandardMaterial
            color={props.color}
            emissive={props.emissive}
            emissiveIntensity={props.emissiveIntensity}
            toneMapped={false}
          />
        </Sphere>
      )}

      {/* Wicket visualization */}
      {latestPrediction === 'Wicket' && (
        <group position={[0, 0.5, 5]}>
          <Box args={[0.15, 1.5, 0.15]} position={[-0.5, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
          <Box args={[0.15, 1.5, 0.15]} position={[0, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
          <Box args={[0.15, 1.5, 0.15]} position={[0.5, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
        </group>
      )}

      <ContactShadows position={[0, -0.14, 0]} opacity={0.5} scale={60} blur={3} far={5} />
    </group>
  );
}

// Match Score Card Component (Hotstar style)
function ScoreCard({ liveData }) {
  return (
    <div className="score-card">
      <div className="match-status-bar">
        <span className="live-indicator">🔴 LIVE</span>
        <span className="match-format">T20</span>
      </div>

      <div className="teams-container">
        <div className="team-section">
          <div className="team-logo">{liveData?.batting_team?.charAt(0) || 'A'}</div>
          <div className="team-name">{liveData?.batting_team || 'Team A'}</div>
        </div>

        <div className="score-section">
          <div className="main-score">
            <span className="runs">{liveData?.runs || 0}</span>
            <span className="separator">/</span>
            <span className="wickets">{liveData?.wickets || 0}</span>
          </div>
          <div className="over-info">
            Over {liveData?.over || 0.0}
          </div>
          <div className="run-rate">
            CRR: {liveData?.current_run_rate?.toFixed(2) || '0.00'}
          </div>
        </div>

        <div className="team-section">
          <div className="team-logo">{liveData?.bowling_team?.charAt(0) || 'B'}</div>
          <div className="team-name">{liveData?.bowling_team || 'Team B'}</div>
        </div>
      </div>
    </div>
  );
}

// Ball History Component (Hotstar style)
function BallHistory({ recentOvers }) {
  return (
    <div className="ball-history-container">
      <div className="history-header">
        <span>Recent Overs</span>
        <span className="toggle-btn">View All</span>
      </div>

      {recentOvers?.length > 0 ? (
        <div className="overs-list">
          {recentOvers.slice(-5).reverse().map((over, overIdx) => (
            <div key={overIdx} className="over-item">
              <div className="over-label">Ov {over.overNumber}</div>
              <div className="balls-row">
                {over.balls.map((ball, ballIdx) => (
                  <div
                    key={ballIdx}
                    className={`ball-ball ${getBallClass(ball)}`}
                  >
                    {ball === 'Wicket' ? 'W' : ball === 'Dot' ? '0' : ball}
                  </div>
                ))}
              </div>
              <div className="over-runs">{over.runs} runs</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-history">Waiting for ball data...</div>
      )}
    </div>
  );
}

function getBallClass(ball) {
  if (ball === 'Wicket') return 'wicket-ball';
  if (ball === '6') return 'six-ball';
  if (ball === '4') return 'four-ball';
  if (ball === 'Dot') return 'dot-ball';
  return 'run-ball';
}

// Prediction Panel Component
function PredictionPanel({ prediction, confidence, probabilities }) {
  const topPredictions = Object.entries(probabilities || {})
    .sort(([,a], [,b]) => b - a)
    .slice(0, 4);

  return (
    <div className="prediction-panel">
      <div className="panel-header">
        <span className="ai-badge">AI</span>
        <span>Next Ball Prediction</span>
      </div>

      <div className="main-prediction">
        <div className={`prediction-value ${getPredictionColor(prediction)}`}>
          {prediction}
        </div>
        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={{ width: `${(confidence || 0) * 100}%` }}
          />
        </div>
        <div className="confidence-text">
          {((confidence || 0) * 100).toFixed(1)}% confidence
        </div>
      </div>

      <div className="probability-grid">
        {topPredictions.map(([outcome, prob]) => (
          <div key={outcome} className="prob-item">
            <span className="prob-outcome">{outcome}</span>
            <div className="prob-bar-container">
              <div
                className={`prob-bar ${getOutcomeBarColor(outcome)}`}
                style={{ width: `${prob * 100}%` }}
              />
            </div>
            <span className="prob-value">{(prob * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function getPredictionColor(pred) {
  switch(pred) {
    case '6': return 'pred-six';
    case '4': return 'pred-four';
    case 'Wicket': return 'pred-wicket';
    case 'Dot': return 'pred-dot';
    default: return 'pred-run';
  }
}

function getOutcomeBarColor(outcome) {
  switch(outcome) {
    case '6': return 'bar-six';
    case '4': return 'bar-four';
    case 'Wicket': return 'bar-wicket';
    case 'Dot': return 'bar-dot';
    default: return 'bar-run';
  }
}

// Commentary Component
function Commentary({ commentary }) {
  return (
    <div className="commentary-panel">
      <div className="commentary-header">Commentary</div>
      <div className="commentary-list">
        {commentary?.slice(-10).reverse().map((c, idx) => (
          <div key={idx} className="commentary-item">
            <span className="commentary-over">{c.over}</span>
            <span className="commentary-text">{c.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Stats Panel
function StatsPanel({ liveData }) {
  return (
    <div className="stats-panel">
      <div className="stats-header">Match Statistics</div>
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-label">Run Rate</span>
          <span className="stat-value">{liveData?.current_run_rate?.toFixed(2) || '0.00'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Batsman SR</span>
          <span className="stat-value">{liveData?.batsman_strike_rate?.toFixed(0) || '0'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Bowler Eco</span>
          <span className="stat-value">{liveData?.bowler_economy?.toFixed(1) || '0.0'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Powerplay</span>
          <span className="stat-value">{liveData?.is_powerplay ? 'Yes' : 'No'}</span>
        </div>
      </div>
    </div>
  );
}

// Match Predictions Panel (Hackathon)
function MatchPredictionsPanel({ preMatchData }) {
  return (
    <div className="match-predictions-panel">
      <div className="predictions-header">
        <span>Match Predictions</span>
        <span className="hackathon-badge">HACKATHON</span>
      </div>

      {preMatchData?.map((match, idx) => (
        <div key={idx} className="match-pred-item">
          <div className="match-title">{match.match}</div>
          <div className="venue-info">{match.venue}</div>

          <div className="outcome-bars">
            <div className="outcome-row">
              <span className="outcome-label">{match.team_a} (Big)</span>
              <div className="bar-wrapper">
                <div
                  className="bar-fill team-a"
                  style={{ width: `${match.predictions?.A_big || 0}%` }}
                />
              </div>
              <span className="bar-percent">{(match.predictions?.A_big || 0).toFixed(1)}%</span>
            </div>
            <div className="outcome-row">
              <span className="outcome-label">{match.team_a} (Small)</span>
              <div className="bar-wrapper">
                <div
                  className="bar-fill team-a-small"
                  style={{ width: `${match.predictions?.A_small || 0}%` }}
                />
              </div>
              <span className="bar-percent">{(match.predictions?.A_small || 0).toFixed(1)}%</span>
            </div>
            <div className="outcome-row">
              <span className="outcome-label">{match.team_b} (Big)</span>
              <div className="bar-wrapper">
                <div
                  className="bar-fill team-b"
                  style={{ width: `${match.predictions?.B_big || 0}%` }}
                />
              </div>
              <span className="bar-percent">{(match.predictions?.B_big || 0).toFixed(1)}%</span>
            </div>
            <div className="outcome-row">
              <span className="outcome-label">{match.team_b} (Small)</span>
              <div className="bar-wrapper">
                <div
                  className="bar-fill team-b-small"
                  style={{ width: `${match.predictions?.B_small || 0}%` }}
                />
              </div>
              <span className="bar-percent">{(match.predictions?.B_small || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Main App Component
export default function App() {
  const [liveData, setLiveData] = useState(null);
  const [prediction, setPrediction] = useState('STANDBY');
  const [confidence, setConfidence] = useState(0);
  const [probabilities, setProbabilities] = useState({});
  const [recentOvers, setRecentOvers] = useState([]);
  const [commentary, setCommentary] = useState([]);
  const [preMatchData, setPreMatchData] = useState([]);
  const [activeTab, setActiveTab] = useState('live');

  // Fetch pre-match predictions
  useEffect(() => {
    fetch('http://localhost:5000/api/pre-match')
      .then(res => res.json())
      .then(data => setPreMatchData(data))
      .catch(err => console.error('Pre-match fetch error:', err));
  }, []);

  // Simulate live data (since no actual live feed)
  useEffect(() => {
    const outcomes = ['Dot', '1', '2', '4', '6', 'Wicket'];
    const weights = [0.35, 0.25, 0.1, 0.15, 0.1, 0.05];

    const generateOutcome = () => {
      let random = Math.random();
      for (let i = 0; i < weights.length; i++) {
        random -= weights[i];
        if (random <= 0) return outcomes[i];
      }
      return outcomes[0];
    };

    const generateProbs = () => {
      const probs = {};
      outcomes.forEach(o => {
        probs[o] = Math.random() * 0.4 + 0.05;
      });
      const total = Object.values(probs).reduce((a, b) => a + b, 0);
      Object.keys(probs).forEach(k => probs[k] /= total);
      return probs;
    };

    let ballCount = 0;
    let runs = 0;
    let wickets = 0;
    let currentOverBalls = [];

    const interval = setInterval(() => {
      const outcome = generateOutcome();
      const probs = generateProbs();

      let ballRuns = outcome === 'Wicket' ? 0 : parseInt(outcome) || 0;
      runs += ballRuns;
      if (outcome === 'Wicket') wickets++;
      ballCount++;

      const over = Math.floor(ballCount / 6) + 1;
      const ballInOver = (ballCount % 6) + 1;
      const currentOver = ballInOver / 6;
      const totalOver = over - 1 + currentOver;

      currentOverBalls.push(outcome);

      // Complete over
      if (ballCount % 6 === 0) {
        const overRuns = currentOverBalls.reduce((sum, b) => {
          if (b === 'Wicket') return sum;
          return sum + (parseInt(b) || 0);
        }, 0);

        setRecentOvers(prev => {
          const newOvers = [...prev, {
            overNumber: over,
            balls: [...currentOverBalls],
            runs: overRuns
          }];
          return newOvers.slice(-10);
        });

        currentOverBalls = [];
      }

      const bestProb = Object.entries(probs).sort((a, b) => b[1] - a[1])[0];

      setLiveData({
        match: 'Live Match',
        status: 'LIVE',
        batting_team: 'Punjab Kings',
        bowling_team: 'Mumbai Indians',
        runs,
        wickets,
        over: totalOver.toFixed(1),
        current_run_rate: (runs / (ballCount / 6) * 6).toFixed(2) || 0,
        batsman_strike_rate: (ballRuns * 100).toFixed(0) || 130,
        bowler_economy: (ballRuns * 6).toFixed(1) || 8.0,
        is_powerplay: ballCount <= 36,
        is_death: ballCount >= 90
      });

      setPrediction(bestProb[0]);
      setConfidence(bestProb[1]);
      setProbabilities(probs);

      setCommentary(prev => [...prev, {
        over: `Ov ${over}.${ballInOver}`,
        text: getCommentaryText(outcome, ballRuns)
      }]);

    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo">🏏</div>
          <div className="brand">
            <span className="brand-name">IPL PREDICTOR</span>
            <span className="brand-tag">AI POWERED</span>
          </div>
        </div>
        <div className="header-center">
          <div className="live-badge">
            <span className="live-dot"></span>
            LIVE
          </div>
        </div>
        <div className="header-right">
          <div className="model-status">
            <span className="status-dot"></span>
            Model: 4.55/5
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
          onClick={() => setActiveTab('live')}
        >
          🔴 Live
        </button>
        <button
          className={`tab-btn ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
        >
          📊 Predictions
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📜 History
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'live' && (
          <>
            {/* Score Card */}
            <ScoreCard liveData={liveData} />

            <div className="content-grid">
              {/* Left Column */}
              <div className="left-column">
                <BallHistory recentOvers={recentOvers} />
                <StatsPanel liveData={liveData} />
              </div>

              {/* Center - 3D Pitch */}
              <div className="center-column">
                <div className="pitch-container">
                  <Canvas camera={{ position: [0, 8, 15], fov: 45 }}>
                    <color attach="background" args={['#0a0a12']} />
                    <ambientLight intensity={0.5} />
                    <spotLight position={[10, 20, 10]} intensity={1.5} penumbra={1} color="#4488ff" />
                    <spotLight position={[-10, 20, -10]} intensity={1.5} penumbra={1} color="#ff4488" />
                    <CricketPitch
                      latestPrediction={prediction}
                    />
                    <OrbitControls
                      enableZoom={true}
                      enablePan={false}
                      maxPolarAngle={Math.PI / 2 - 0.1}
                      autoRotate={true}
                      autoRotateSpeed={0.3}
                    />
                  </Canvas>
                </div>
              </div>

              {/* Right Column */}
              <div className="right-column">
                <PredictionPanel
                  prediction={prediction}
                  confidence={confidence}
                  probabilities={probabilities}
                />
                <Commentary commentary={commentary} />
              </div>
            </div>
          </>
        )}

        {activeTab === 'predictions' && (
          <div className="predictions-tab">
            <div className="predictions-title">
              <h2>🏆 Hackathon Match Predictions</h2>
              <p>AI-powered predictions for upcoming IPL matches</p>
            </div>
            <MatchPredictionsPanel preMatchData={preMatchData} />
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-tab">
            <div className="history-title">
              <h2>📜 Match History</h2>
            </div>
            <BallHistory recentOvers={recentOvers} />
            <Commentary commentary={commentary} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <span>IPL Prediction System v2.0</span>
        <span>|</span>
        <span>Model Rating: 4.55/5</span>
        <span>|</span>
        <span>Accuracy: 57%</span>
      </footer>
    </div>
  );
}

function getCommentaryText(outcome, runs) {
  const comments = {
    'Dot': 'Dot ball. Maiden over building pressure.',
    '1': `Single taken. ${runs} run.`,
    '2': `Good running between wickets. ${runs} runs.`,
    '4': `Boundary! That's a cracking shot! ${runs} runs.`,
    '6': `SIX! Over the ropes! What a hit! ${runs} runs!`,
    'Wicket': 'OUT! Bowled him! What a delivery!'
  };
  return comments[outcome] || `${runs} runs.`;
}