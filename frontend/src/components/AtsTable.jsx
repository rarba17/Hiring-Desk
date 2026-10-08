import { useEffect, useState } from 'react';
import { api } from '../api.js';

export function AtsTable({ refreshKey }) {
  const [rows, setRows] = useState([]);
  const [role, setRole] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const load = async () => {
    setBusy(true); setMsg('');
    try {
      const j = await api.ats(role);
      const list = j.candidates || [];
      setRows(list);
      setMsg(`${list.length} candidate(s)${role ? ` matching "${role}"` : ''}`);
    } catch (e) { setMsg(`refresh failed: ${e.message || e}`); }
    finally { setBusy(false); }
  };
  useEffect(() => { load(); }, [refreshKey]);
  return (
    <div className="card">
      <h3>2 · ATS (verification)</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        <input placeholder="filter role (optional)" value={role} onChange={(e) => setRole(e.target.value)} />
        <button type="button" className="ghost" onClick={load} disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button>
      </div>
      {msg && <p><small style={{ color: '#93a4bb' }}>{msg}</small></p>}
      <table><thead><tr><th>Candidate</th><th>Score</th><th>Stage</th><th>Slot</th></tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.candidate_id}><td>{r.name}<br /><small>{r.candidate_id}</small></td><td>{r.score}</td>
        <td className={`stage-${r.stage}`}>{r.stage}</td><td>{r.slot || '—'}</td></tr>
      ))}</tbody></table>
      {!rows.length && !busy && <p style={{ color: '#93a4bb' }}>No rows yet — run a task above first.</p>}
    </div>
  );
}
