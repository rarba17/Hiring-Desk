import { useEffect, useState } from 'react';
import { api } from '../api.js';

export function AtsTable({ refreshKey }) {
  const [rows, setRows] = useState([]);
  const [role, setRole] = useState('');
  const load = async () => {
    const j = await api.ats(role);
    setRows(j.candidates || []);
  };
  useEffect(() => { load(); }, [refreshKey]);
  return (
    <div className="card">
      <h3>2 · ATS (verification)</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        <input placeholder="filter role (optional)" value={role} onChange={(e) => setRole(e.target.value)} />
        <button className="ghost" onClick={load}>Refresh</button>
      </div>
      <table><thead><tr><th>Candidate</th><th>Score</th><th>Stage</th><th>Slot</th></tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.candidate_id}><td>{r.name}<br /><small>{r.candidate_id}</small></td><td>{r.score}</td>
        <td className={`stage-${r.stage}`}>{r.stage}</td><td>{r.slot || '—'}</td></tr>
      ))}</tbody></table>
      {!rows.length && <p style={{ color: '#93a4bb' }}>No rows yet — run a task.</p>}
    </div>
  );
}
