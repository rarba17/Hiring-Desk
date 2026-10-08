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
      <header className="masthead">
        <div className="masthead-row">
          <div>
            <span className="folder-tab">Interview dossier</span>
            <h1>Hiring desk</h1>
          </div>
          <span className={`seal ${ok ? 'ok' : ''}`}>{ok === null ? 'Checking line' : ok ? 'Line open' : 'Line down — start uvicorn :8000'}</span>
        </div>
      </header>
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
      <p className="desk-note">Tip: set SCORE_THRESHOLD=95 in .env to force approval. Block a slot in calendars/ to see re-planning.</p>
    </div>
  );
}
