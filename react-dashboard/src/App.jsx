import { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Sphere, ContactShadows } from '@react-three/drei';
import './App.css';

// 3D Pitch Component
function CricketPitch({ latestPrediction }) {
  return (
    <group position={[0, -1, 0]}>
      {/* The Pitch */}
      <Box args={[4, 0.2, 12]} position={[0, -0.1, 0]}>
        <meshStandardMaterial color="#8B7355" roughness={0.8} /> 
      </Box>
      
      {/* The Grass */}
      <Box args={[30, 0.1, 30]} position={[0, -0.15, 0]}>
        <meshStandardMaterial color="#1a3d1a" roughness={1} />
      </Box>

      {/* Dynamic Visualizations */}
      {latestPrediction === 'Dot' && (
        <Sphere args={[0.2, 16, 16]} position={[0, 0, 4]}>
          <meshStandardMaterial color="#888888" />
        </Sphere>
      )}

      {latestPrediction === '1' && (
        <Sphere args={[0.2, 32, 32]} position={[-2, 0, 0]}>
          <meshStandardMaterial color="#0088ff" emissive="#0088ff" emissiveIntensity={2} />
        </Sphere>
      )}

      {latestPrediction === '2' && (
        <Sphere args={[0.2, 32, 32]} position={[-4, 0, -2]}>
          <meshStandardMaterial color="#00ffcc" emissive="#00ffcc" emissiveIntensity={2} />
        </Sphere>
      )}

      {latestPrediction === '4' && (
        <Box args={[0.5, 0.1, 2]} position={[6, -0.05, 6]} rotation={[0, Math.PI/4, 0]}>
          <meshStandardMaterial color="#ffcc00" emissive="#ffcc00" emissiveIntensity={3} />
        </Box>
      )}

      {latestPrediction === '6' && (
        <Sphere args={[0.4, 32, 32]} position={[0, 10, -12]}>
          <meshStandardMaterial color="#ff0055" emissive="#ff0055" emissiveIntensity={4} toneMapped={false} />
        </Sphere>
      )}

      {latestPrediction === 'Wicket' && (
        <group position={[0, 0.5, 5]}>
          <Box args={[0.1, 1.5, 0.1]} position={[-0.2, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
          <Box args={[0.1, 1.5, 0.1]} position={[0, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
          <Box args={[0.1, 1.5, 0.1]} position={[0.2, 0, 0]}><meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={5} /></Box>
        </group>
      )}
      
      <ContactShadows position={[0, -0.14, 0]} opacity={0.4} scale={40} blur={2} far={4} />
    </group>
  );
}

export default function PredictionDashboard() {
  const [prediction, setPrediction] = useState("STANDBY");
  const [confidence, setConfidence] = useState("0.0");
  const [matchStatus, setMatchStatus] = useState("AWAITING LIVE FEED");
  
  const [timeUntilMatch, setTimeUntilMatch] = useState("0h 0m 0s");
  const [preMatchData, setPreMatchData] = useState([]);
  const [liveData, setLiveData] = useState(null);

  // Countdown Timer Implementation
  useEffect(() => {
    const matchDate = new Date("2026-05-14T19:00:00+05:30"); // 7 PM Tonight
    const interval = setInterval(() => {
      const now = new Date();
      const diff = matchDate - now;
      if (diff > 0) {
        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        setTimeUntilMatch(`${h}h ${m}m ${s}s`);
      } else {
        setTimeUntilMatch("MATCH IS LIVE");
        setMatchStatus("LIVE FEED CONNECTED");
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch Pre-Match Hackathon Predictions
  useEffect(() => {
    fetch('http://localhost:5000/api/pre-match')
      .then(res => res.json())
      .then(data => setPreMatchData(data))
      .catch(err => console.error("Pre-match fetch failed:", err));
  }, []);

  // Poll Live Data
  useEffect(() => {
    const interval = setInterval(() => {
      fetch('http://localhost:5000/api/live')
        .then(res => res.json())
        .then(data => {
            setLiveData(data);
            if (data.last_prediction) {
                setPrediction(data.last_prediction.outcome);
                setConfidence(data.last_prediction.probs[data.last_prediction.outcome]);
            }
        })
        .catch(err => console.error("Live fetch failed:", err));
    }, 2000);
    return () => clearInterval(interval);
  }, []);


  const getPredictionColorClass = (pred) => {
      if (pred === 'Wicket') return 'text-red';
      if (pred === '6') return 'text-pink';
      if (pred === '4') return 'text-yellow';
      if (pred === 'Dot') return 'text-gray';
      return 'text-cyan';
  }

  const getTimelineDotClass = (run) => {
      if (run === 'Wicket') return 'timeline-w';
      if (run === '6') return 'timeline-6';
      if (run === '4') return 'timeline-4';
      if (run === 'Dot') return 'timeline-dot';
      return 'timeline-run';
  }

  return (
    <div className="dashboard-container">
      <div className="glow-orb orb-1"></div>
      <div className="glow-orb orb-2"></div>
      
      <header className="glass-header">
        <div className="header-brand">
          <h1>IPL PREDICTOR <span className="badge">PRO</span></h1>
          <p className="subtitle">NEXT: PBKS vs DC • DHARAMSALA</p>
        </div>
        
        {/* Scheduler Widget */}
        <div className="scheduler-widget">
            <div className="sched-label">LIVE MATCH STARTS IN:</div>
            <div className={`sched-time ${timeUntilMatch === 'MATCH IS LIVE' ? 'text-green' : 'text-white'}`}>
                {timeUntilMatch}
            </div>
        </div>
      </header>

      <div className="main-layout">
        <div className="glass-panel sidebar">
          <div className="status-indicator">
            <div className={`led ${liveData && liveData.status === 'LIVE' ? 'led-active' : 'led-standby'}`}></div>
            <span>{liveData ? `${liveData.match} - ${liveData.status}` : matchStatus}</span>
          </div>
          
          {liveData && liveData.status === 'LIVE' && (
            <div className="score-widget">
                <h2>{liveData.runs}/{liveData.wickets}</h2>
                <p>Over: {liveData.over} • CRR: {liveData.current_run_rate}</p>
                <div className="overs-timeline">
                    {liveData.recent_overs && liveData.recent_overs.map((ovr, i) => (
                        <div key={i} className="over-group">
                            <span className="over-label">Ov {liveData.over - liveData.recent_overs.length + i + 1}</span>
                            <div className="balls-row">
                                {ovr.map((ball, j) => (
                                    <div key={j} className={`timeline-ball ${getTimelineDotClass(ball)}`}>
                                        {ball === 'Wicket' ? 'W' : (ball === 'Dot' ? '0' : ball)}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
          )}

          <div className="prediction-card">
            <p className="label">NEXT BALL PREDICTION</p>
            <h1 className={`prediction-value ${getPredictionColorClass(prediction)}`}>
              {prediction}
            </h1>
            <p className="confidence">
              CONFIDENCE <span className="conf-value">{confidence}%</span>
            </p>
            {liveData && liveData.last_prediction && liveData.last_prediction.historical_context && (
                <div className="historical-context">
                    <p>{liveData.last_prediction.historical_context}</p>
                </div>
            )}
          </div>

          <div className="pre-match-panel">
            <h3>HACKATHON PREDICTIONS</h3>
            {Array.isArray(preMatchData) && preMatchData.map((m, idx) => (
                <div key={idx} className="pre-match-item">
                    <h4>{m.match}</h4>
                    <div className="prob-bars">
                        <div className="prob-row">
                            <div className="bar-label"><span>{m.team_a} (Big)</span> <span>{m.predictions.A_big}%</span></div>
                            <div className="bar-container"><div className="bar-fill bg-a" style={{width: `${m.predictions.A_big}%`}}></div></div>
                        </div>
                        <div className="prob-row">
                            <div className="bar-label"><span>{m.team_a} (Small)</span> <span>{m.predictions.A_small}%</span></div>
                            <div className="bar-container"><div className="bar-fill bg-a" style={{width: `${m.predictions.A_small}%`}}></div></div>
                        </div>
                        <div className="prob-row">
                            <div className="bar-label"><span>{m.team_b} (Big)</span> <span>{m.predictions.B_big}%</span></div>
                            <div className="bar-container"><div className="bar-fill bg-b" style={{width: `${m.predictions.B_big}%`}}></div></div>
                        </div>
                        <div className="prob-row">
                            <div className="bar-label"><span>{m.team_b} (Small)</span> <span>{m.predictions.B_small}%</span></div>
                            <div className="bar-container"><div className="bar-fill bg-b" style={{width: `${m.predictions.B_small}%`}}></div></div>
                        </div>
                    </div>
                </div>
            ))}
          </div>

          <div className="system-notice">
            <p>Live matching will automatically begin once the toss occurs at the venue.</p>
          </div>

          <div className="agent-status">
            <h3>SYSTEM STATUS</h3>
            <ul>
              <li><span className="dot online"></span> Vision Pipeline (YOLOv8)</li>
              <li><span className="dot online"></span> Statistician Agent (GBM)</li>
              <li><span className={`dot ${timeUntilMatch === 'MATCH IS LIVE' ? 'online' : 'standby'}`}></span> Live API Feed</li>
            </ul>
          </div>
        </div>

        <div className="canvas-container">
          <Canvas camera={{ position: [0, 8, 15], fov: 45 }}>
            <color attach="background" args={['#050508']} />
            <ambientLight intensity={0.4} />
            <spotLight position={[10, 20, 10]} intensity={1.5} penumbra={1} color="#4488ff" />
            <spotLight position={[-10, 20, -10]} intensity={1.5} penumbra={1} color="#ff4488" />
            <CricketPitch latestPrediction={prediction} />
            <OrbitControls enableZoom={true} enablePan={false} maxPolarAngle={Math.PI / 2 - 0.1} autoRotate={true} autoRotateSpeed={0.5} />
          </Canvas>
          <div className="canvas-overlay">
            Interactive 3D Engine • Drag to rotate
          </div>
          
          {/* Key Legend */}
          <div className="legend-panel">
            <div className="legend-item"><span className="legend-color" style={{background: '#ff0055'}}></span> 6 Runs (High)</div>
            <div className="legend-item"><span className="legend-color" style={{background: '#ffcc00'}}></span> 4 Runs (Ground)</div>
            <div className="legend-item"><span className="legend-color" style={{background: '#00ffcc'}}></span> 2 Runs</div>
            <div className="legend-item"><span className="legend-color" style={{background: '#0088ff'}}></span> 1 Run</div>
            <div className="legend-item"><span className="legend-color" style={{background: '#888888'}}></span> Dot Ball</div>
            <div className="legend-item"><span className="legend-color" style={{background: '#ff0000'}}></span> Wicket</div>
          </div>
        </div>
      </div>
    </div>
  );
}
