import { useEffect, useState } from 'react';
import { api } from './api.js';
import { TaskRunner } from './components/TaskRunner.jsx';
import { AtsTable } from './components/AtsTable.jsx';
import { JdManager } from './components/JdManager.jsx';
import { ResumeUpload } from './components/ResumeUpload.jsx';
import './index.css';

export default function App() {
  const [ok, setOk] = useState(null);
  const [tick, setTick] = useState(0);
  const bump = () => setTick((t) => t + 1);
  useEffect(() => { api.health().then(() => setOk(true)).catch(() => setOk(false)); }, []);
  return (
    <div className="app">
      <div className="top">
        <h1>Hiring Worker Console</h1>
        <span className={`badge ${ok ? 'ok' : ''}`}>{ok === null ? '…' : ok ? 'backend: ok' : 'backend: down (run uvicorn :8000)'}</span>
      </div>
      <div className="grid">
        <div>
          <TaskRunner onDone={bump} />
          <ResumeUpload onDone={bump} />
        </div>
        <div>
          <AtsTable refreshKey={tick} />
          <JdManager />
        </div>
      </div>
      <p style={{ color: '#93a4bb' }}><small>Tip: set SCORE_THRESHOLD=95 in .env to force approval. Block a slot in calendars/ to see re-planning.</small></p>
    </div>
  );
}
