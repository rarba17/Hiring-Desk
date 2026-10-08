import { useEffect, useState } from 'react';
import { api } from './api.js';
import { TaskRunner } from './components/TaskRunner.jsx';
import { AtsTable } from './components/AtsTable.jsx';
import { JdManager } from './components/JdManager.jsx';
import { ResumeUpload } from './components/ResumeUpload.jsx';
import { Landing } from './components/Landing.jsx';
import './index.css';

function Console() {
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
          <div className="masthead-side">
            <span className={`seal ${ok ? 'ok' : ''}`}>{ok === null ? 'Checking line' : ok ? 'Line open' : 'Line down — start uvicorn :8000'}</span>
            <a className="backlink" href="#/">Overview</a>
          </div>
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

export default function App() {
  const [route, setRoute] = useState(window.location.hash || '#/');
  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  if (route.startsWith('#/console')) return <Console />;
  return <Landing />;
}
