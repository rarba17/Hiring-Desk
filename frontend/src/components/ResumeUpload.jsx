import { useState } from 'react';
import { api } from '../api.js';

export function ResumeUpload({ onDone }) {
  const [msg, setMsg] = useState('');
  const send = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const j = await api.uploadResume(f);
      setMsg(`uploaded ${j.filename} (${j.bytes}b)`);
      onDone && onDone();
    } catch (err) { setMsg(String(err.message || err)); }
  };
  return (
    <div className="card">
      <h3>4 · Upload resume (.txt/.md/.pdf)</h3>
      <input type="file" accept=".txt,.md,.pdf" onChange={send} />
      {msg && <p>{msg}</p>}
    </div>
  );
}
