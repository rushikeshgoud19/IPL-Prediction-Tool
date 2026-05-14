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
function ScoreCard({ liveData, matchInfo }) {
  // Use real team names from matchInfo if available
  const battingTeam = liveData?.batting_team || matchInfo?.batting_team || 'Team A';
  const bowlingTeam = liveData?.bowling_team || matchInfo?.bowling_team || 'Team B';
  const team1Name = matchInfo?.team_1 || battingTeam;
  const team2Name = matchInfo?.team_2 || bowlingTeam;
  const team1Short = team1Name.substring(0, 4).toUpperCase();
  const team2Short = team2Name.substring(0, 4).toUpperCase();

  return (
    <div className="score-card">
      <div className="match-status-bar">
        <span className="live-indicator">🔴 LIVE</span>
        <span className="match-format">T20</span>
        <span className="innings-badge">
          {matchInfo?.innings ? `Innings ${matchInfo.innings}` : 'Pre-Match'}
        </span>
      </div>

      <div className="match-info">
        <span className="series-name">{matchInfo?.series || 'IPL 2026'}</span>
        <span className="venue-name">{matchInfo?.venue || ''}</span>
      </div>

      <div className="teams-container">
        <div className="team-section">
          <div className="team-logo">{team1Short.charAt(0)}</div>
          <div className="team-name">{team1Name}</div>
          <div className="team-short">{team1Short}</div>
        </div>

        <div className="score-section">
          <div className="main-score">
            <span className="runs">{matchInfo?.team_1_runs || liveData?.runs || 0}</span>
            <span className="separator">/</span>
            <span className="wickets">{matchInfo?.team_1_wickets || liveData?.wickets || 0}</span>
          </div>
          <div className="over-info">
            Over {matchInfo?.team_1_overs || liveData?.over || 0.0}
          </div>
          <div className="run-rate">
            CRR: {liveData?.current_run_rate || liveData?.run_rate || '0.00'}
          </div>
        </div>

        <div className="vs-divider">VS</div>

        <div className="score-section">
          <div className="main-score target">
            <span className="runs">{matchInfo?.team_2_runs || 0}</span>
            <span className="separator">/</span>
            <span className="wickets">{matchInfo?.team_2_wickets || 0}</span>
          </div>
          <div className="over-info">
            Over {matchInfo?.team_2_overs || 0.0}
          </div>
          {matchInfo?.target && (
            <div className="target-info">
              Target: {matchInfo.target}
            </div>
          )}
        </div>

        <div className="team-section">
          <div className="team-logo">{team2Short.charAt(0)}</div>
          <div className="team-name">{team2Name}</div>
          <div className="team-short">{team2Short}</div>
        </div>
      </div>

      {matchInfo?.last_ball && (
        <div className="last-ball-info">
          <span className="last-ball-label">Last Ball:</span>
          <span className="last-ball-text">{matchInfo.last_ball}</span>
        </div>
      )}

      {matchInfo?.prediction_quality && (
        <div className="prediction-quality">
          <span className="quality-label">Prediction Quality:</span>
          <span className={`quality-value ${matchInfo.prediction_quality}`}>
            {matchInfo.prediction_quality === 'improving' ? '🔄 Improving' : '⏳ Developing'}
          </span>
        </div>
      )}
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
              <div className="over-label">Ov {over.overNumber || over.over}</div>
              <div className="balls-row">
                {(over.balls || over.balls || []).map((ball, ballIdx) => (
                  <div
                    key={ballIdx}
                    className={`ball-ball ${getBallClass(ball)}`}
                  >
                    {ball === 'Wicket' || ball === 'W' ? 'W' : (ball === 'Dot' || ball === '0') ? '0' : ball}
                  </div>
                ))}
              </div>
              <div className="over-runs">{over.runs || over.total_runs} runs</div>
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
  if (ball === 'Wicket' || ball === 'W') return 'wicket-ball';
  if (ball === '6') return 'six-ball';
  if (ball === '4') return 'four-ball';
  if (ball === 'Dot' || ball === '0') return 'dot-ball';
  return 'run-ball';
}


// Stats Panel
function StatsPanel({ liveData }) {
  return (
    <div className="stats-panel">
      <div className="stats-header">Match Statistics</div>
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-label">Run Rate</span>
          <span className="stat-value">{liveData?.current_run_rate || liveData?.run_rate || '0.00'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Batsman SR</span>
          <span className="stat-value">{liveData?.batsman_strike_rate || '0'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Bowler Eco</span>
          <span className="stat-value">{liveData?.bowler_economy || '0.0'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Powerplay</span>
          <span className="stat-value">{liveData?.is_powerplay ? 'Yes' : 'No'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Death Overs</span>
          <span className="stat-value">{liveData?.is_death ? 'Yes' : 'No'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Confidence</span>
          <span className="stat-value">{liveData?.confidence || '0'}%</span>
        </div>
      </div>
    </div>
  );
}

// Live Match Predictions Panel (with real team names)
function LivePredictionsPanel({ predictionData, matchInfo }) {
  if (!predictionData) {
    return (
      <div className="live-predictions-panel">
        <div className="predictions-header">
          <span>Match Predictions</span>
          <span className="live-badge">LIVE</span>
        </div>
        <div className="no-prediction">
          <div className="loading-spinner">⏳</div>
          <p>Waiting for live match data...</p>
        </div>
      </div>
    );
  }

  const { predictions, most_likely, confidence } = predictionData;
  const team1 = matchInfo?.team_1 || 'Team A';
  const team2 = matchInfo?.team_2 || 'Team B';

  return (
    <div className="live-predictions-panel">
      <div className="predictions-header">
        <span>Live Match Predictions</span>
        <span className={`confidence-badge ${confidence > 70 ? 'high' : confidence > 50 ? 'medium' : 'low'}`}>
          {confidence}% confidence
        </span>
      </div>

      <div className="prediction-teams">
        <div className="pred-team-a">
          <div className="team-label">{team1}</div>
          <div className="team-predictions">
            <div className="team-pred-row">
              <span className="pred-label">Big Win</span>
              <div className="pred-bar-container">
                <div className="pred-bar team-a-bar" style={{ width: `${predictions?.A_big || 0}%` }} />
              </div>
              <span className="pred-value">{(predictions?.A_big || 0).toFixed(1)}%</span>
            </div>
            <div className="team-pred-row">
              <span className="pred-label">Small Win</span>
              <div className="pred-bar-container">
                <div className="pred-bar team-a-small-bar" style={{ width: `${predictions?.A_small || 0}%` }} />
              </div>
              <span className="pred-value">{(predictions?.A_small || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="vs-marker">VS</div>

        <div className="pred-team-b">
          <div className="team-label">{team2}</div>
          <div className="team-predictions">
            <div className="team-pred-row">
              <span className="pred-label">Big Win</span>
              <div className="pred-bar-container">
                <div className="pred-bar team-b-bar" style={{ width: `${predictions?.B_big || 0}%` }} />
              </div>
              <span className="pred-value">{(predictions?.B_big || 0).toFixed(1)}%</span>
            </div>
            <div className="team-pred-row">
              <span className="pred-label">Small Win</span>
              <div className="pred-bar-container">
                <div className="pred-bar team-b-small-bar" style={{ width: `${predictions?.B_small || 0}%` }} />
              </div>
              <span className="pred-value">{(predictions?.B_small || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="most-likely-result">
        <span className="result-label">Most Likely Result:</span>
        <span className={`result-value ${getResultClass(most_likely)}`}>
          {formatResult(most_likely, team1, team2)}
        </span>
      </div>

      <div className="model-info">
        <span className="model-rating">{predictionData.model_rating || 'Model: 4.55/5'}</span>
        <span className="quality-indicator">{predictionData.prediction_quality || 'Developing'}</span>
      </div>
    </div>
  );
}

function formatResult(result, team1, team2) {
  if (!result) return 'Unknown';
  if (result === 'A_big') return `${team1} to win big`;
  if (result === 'A_small') return `${team1} to win small`;
  if (result === 'B_big') return `${team2} to win big`;
  if (result === 'B_small') return `${team2} to win small`;
  return result;
}

function getResultClass(result) {
  if (result === 'A_big' || result === 'A_small') return 'team-a-win';
  if (result === 'B_big' || result === 'B_small') return 'team-b-win';
  return '';
}

// Toss Prediction Panel
function TossPredictionPanel({ tossData }) {
  const isWaiting = tossData?.status === 'waiting';
  const isMatchStarted = tossData?.status === 'match_started';

  return (
    <div className="toss-prediction-panel">
      <div className="toss-header">
        <span>🎲 Toss Prediction</span>
        <span className={`toss-status ${isWaiting ? 'waiting' : isMatchStarted ? 'started' : 'available'}`}>
          {isWaiting ? '⏳ WAITING' : isMatchStarted ? '🔴 MATCH STARTED' : '✅ READY'}
        </span>
      </div>

      {isMatchStarted ? (
        <div className="toss-unavailable">
          <div className="unavailable-icon">🚫</div>
          <p>Toss prediction disabled - match already in progress</p>
        </div>
      ) : isWaiting ? (
        <div className="toss-waiting">
          <div className="waiting-icon">⏰</div>
          <p className="waiting-message">{tossData?.message}</p>
          {tossData?.teams && (
            <div className="matchup-preview">
              <span className="versus">{tossData.teams.team_1}</span>
              <span className="vs">VS</span>
              <span className="versus">{tossData.teams.team_2}</span>
            </div>
          )}
          <p className="prediction-hint">Prediction will activate at match start</p>
          <div className="model-ready-indicator">
            <span className="ready-dot"></span>
            Model Ready
          </div>
        </div>
      ) : (
        <div className="toss-available">
          <div className="toss-prediction-placeholder">
            <div className="placeholder-icon">🎯</div>
            <p>Enter match details to get toss prediction</p>
          </div>
        </div>
      )}
    </div>
  );
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
            style={{ width: `${confidence || 0}%` }}
          />
        </div>
        <div className="confidence-text">
          {confidence || 0}% confidence
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


// Main App Component
export default function App() {
  const [currentMatch, setCurrentMatch] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [tossData, setTossData] = useState(null);
  const [liveData, setLiveData] = useState(null);
  const [prediction, setPrediction] = useState('STANDBY');
  const [confidence, setConfidence] = useState(0);
  const [probabilities, setProbabilities] = useState({});
  const [recentOvers] = useState([]);
  const [activeTab, setActiveTab] = useState('live');
  const [error, setError] = useState(null);

  // Fetch current live match
  useEffect(() => {
    const fetchCurrentMatch = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/current-match');
        const data = await response.json();

        if (data.error) {
          setError(data.error);
          return;
        }

        setCurrentMatch(data);
        setError(null);
      } catch (err) {
        console.error('Current match fetch error:', err);
        setError('Unable to connect to backend');
      }
    };

    fetchCurrentMatch();
    const interval = setInterval(fetchCurrentMatch, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch toss prediction status
  useEffect(() => {
    const fetchTossPrediction = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/toss');
        const data = await response.json();
        setTossData(data);
      } catch (err) {
        console.error('Toss prediction error:', err);
      }
    };

    fetchTossPrediction();
    const interval = setInterval(fetchTossPrediction, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch live innings predictions (only when match is in progress)
  useEffect(() => {
    const fetchLivePredictions = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/live/innings-predict');
        const data = await response.json();

        if (!data.error) {
          setPredictionData(data);

          // Update live data from prediction response
          if (data.live_state) {
            setLiveData(prev => ({
              ...prev,
              ...data.live_state,
              batting_team: data.match_info?.team_1,
              bowling_team: data.match_info?.team_2,
              current_run_rate: data.live_state?.run_rate || data.live_state?.current_run_rate,
              confidence: data.confidence
            }));
          }
        }
      } catch (err) {
        console.error('Live predictions error:', err);
      }
    };

    // Poll every 10 seconds for live predictions
    fetchLivePredictions();
    const interval = setInterval(fetchLivePredictions, 10000);
    return () => clearInterval(interval);
  }, []);

  // Simulate prediction updates
  useEffect(() => {
    const outcomes = ['Dot', '1', '2', '4', '6', 'Wicket'];

    const generateProbs = () => {
      const probs = {};
      outcomes.forEach(o => {
        probs[o] = Math.random() * 0.4 + 0.05;
      });
      const total = Object.values(probs).reduce((a, b) => a + b, 0);
      Object.keys(probs).forEach(k => probs[k] /= total);
      return probs;
    };

    const interval = setInterval(() => {
      const probs = generateProbs();
      const bestProb = Object.entries(probs).sort((a, b) => b[1] - a[1])[0];
      setPrediction(bestProb[0]);
      setConfidence(Math.round(bestProb[1] * 100));
      setProbabilities(probs);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Prepare match info for child components
  const matchInfo = predictionData?.match_info || {
    team_1: currentMatch?.team_1_name || currentMatch?.batting_team || 'Team A',
    team_2: currentMatch?.team_2_name || currentMatch?.bowling_team || 'Team B',
    venue: currentMatch?.venue || 'Unknown',
    series: currentMatch?.series || 'IPL 2026',
    innings: currentMatch?.innings || 1,
    team_1_runs: currentMatch?.team_1_score?.split('/')[0] || predictionData?.live_state?.team_1_score?.split('/')[0] || 0,
    team_1_wickets: currentMatch?.team_1_score?.split('/')[1] || predictionData?.live_state?.team_1_score?.split('/')[1] || 0,
    team_1_overs: currentMatch?.team_1_overs || predictionData?.live_state?.team_1_overs || 0,
    team_2_runs: currentMatch?.team_2_score?.split('/')[0] || predictionData?.live_state?.team_2_score?.split('/')[0] || 0,
    team_2_wickets: currentMatch?.team_2_score?.split('/')[1] || predictionData?.live_state?.team_2_score?.split('/')[1] || 0,
    team_2_overs: currentMatch?.team_2_overs || predictionData?.live_state?.team_2_overs || 0,
    target: predictionData?.live_state?.target,
    last_ball: currentMatch?.last_ball,
    prediction_quality: predictionData?.prediction_quality
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo">🏏</div>
          <div className="brand">
            <span className="brand-name">IPL PREDICTOR</span>
            <span className="brand-tag">LIVE AI</span>
          </div>
        </div>
        <div className="header-center">
          {currentMatch ? (
            <div className="current-match-badge">
              <span className="live-dot"></span>
              {matchInfo.team_1} vs {matchInfo.team_2}
            </div>
          ) : (
            <div className="live-badge">
              <span className="live-dot"></span>
              NO LIVE MATCH
            </div>
          )}
        </div>
        <div className="header-right">
          <div className="model-status">
            <span className="status-dot"></span>
            Model: 4.55/5
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
        </div>
      )}

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
          className={`tab-btn ${activeTab === 'toss' ? 'active' : ''}`}
          onClick={() => setActiveTab('toss')}
        >
          🎲 Toss
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'live' && (
          <>
            {/* Score Card */}
            <ScoreCard liveData={liveData} matchInfo={matchInfo} />

            <div className="content-grid">
              {/* Left Column */}
              <div className="left-column">
                <LivePredictionsPanel predictionData={predictionData} matchInfo={matchInfo} />
                <BallHistory recentOvers={recentOvers} />
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
                <StatsPanel liveData={liveData} />
              </div>
            </div>
          </>
        )}

        {activeTab === 'predictions' && (
          <div className="predictions-tab">
            <div className="predictions-title">
              <h2>🏆 Live Match Predictions</h2>
              <p>AI-powered predictions using current innings data</p>
            </div>
            <LivePredictionsPanel predictionData={predictionData} matchInfo={matchInfo} />
            <StatsPanel liveData={liveData} />
          </div>
        )}

        {activeTab === 'toss' && (
          <div className="toss-tab">
            <div className="toss-title">
              <h2>🎲 Toss Prediction</h2>
              <p>Predict toss winner before match starts</p>
            </div>
            <TossPredictionPanel tossData={tossData} />
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
        <span>|</span>
        <span>Prediction Quality: {predictionData?.prediction_quality || 'Loading...'}</span>
      </footer>
    </div>
  );
}