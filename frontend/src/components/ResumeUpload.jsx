import { useState } from 'react';
import { api } from '../api.js';

export function ResumeUpload({ onDone }) {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const send = async () => {
    if (!file) { setMsg('choose a file first'); return; }
    setBusy(true); setMsg('');
    try {
      const j = await api.uploadResume(file);
      setMsg(`uploaded ${j.filename} (${j.bytes}b) — re-run a task to screen it`);
      setFile(null);
      onDone && onDone();
    } catch (err) { setMsg(`upload failed: ${err.message || err}`); }
    finally { setBusy(false); }
  };
  return (
    <div className="card">
      <h3>4 · Upload resume (.txt/.md/.pdf)</h3>
      <input type="file" accept=".txt,.md,.pdf" onChange={(e) => { setFile(e.target.files?.[0] || null); setMsg(''); }} />
      <div style={{ marginTop: 8 }}><button type="button" onClick={send} disabled={busy || !file}>{busy ? 'Uploading…' : 'Upload'}</button></div>
      {msg && <p><small>{msg}</small></p>}
    </div>
  );
}
