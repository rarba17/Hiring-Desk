import { useState } from 'react';
import { api } from '../api.js';

export function TaskRunner({ onDone }) {
  const [goal, setGoal] = useState('Schedule interviews for the top 5 candidates for the software engineer role');
  const [out, setOut] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const run = async () => {
    setBusy(true); setErr('');
    try { const j = await api.runTask(goal); setOut(j); onDone && onDone(); }
    catch (e) { setErr(String(e.message || e)); }
    finally { setBusy(false); }
  };
  const decide = async (d) => {
    if (!out?.task_id) return;
    setBusy(true);
    try { const j = await api.approve(out.task_id, d); setOut(j); onDone && onDone(); }
    catch (e) { setErr(String(e.message || e)); }
    finally { setBusy(false); }
  };
  const status = out?.status || out?.result?.status;
  return (
    <div className="card">
      <h3>1 · Run hiring worker</h3>
      <textarea rows={3} value={goal} onChange={(e) => setGoal(e.target.value)} />
      <div><button onClick={run} disabled={busy}>{busy ? 'Running…' : 'Run worker'}</button>
      {status && <span className={`pill ${status}`}>{status}</span>}</div>
      {err && <p style={{ color: '#ff5d5d' }}>{err}</p>}
      {status === 'need_approval' && (
        <div style={{ marginTop: 8 }}>
          <button className="warn" onClick={() => decide('approved')}>Approve & continue</button>
          <button className="ghost" onClick={() => decide('rejected')}>Reject</button>
        </div>
      )}
      {out && <Bookings out={out} />}
      {out && <details><summary>Trace (evidence)</summary><pre className="trace">{JSON.stringify(out.result?.trace || out.trace, null, 2)}</pre></details>}
    </div>
  );
}

function Bookings({ out }) {
  const r = out.result || {};
  const bookings = r.bookings || [];
  const shortlist = (r.trace || []).find((t) => t.shortlist)?.shortlist || [];
  if (!bookings.length && !shortlist.length) return null;
  return (
    <div style={{ marginTop: 12 }}>
      {!!shortlist.length && (<><h4>Shortlist (ranked)</h4><table><thead><tr><th>Candidate</th><th>Score</th><th>Reason</th></tr></thead>
      <tbody>{shortlist.map((s) => <tr key={s.candidate_id}><td>{s.name} ({s.candidate_id})</td><td>{s.score}</td><td>{s.reason || ''}</td></tr>)}</tbody></table></>)}
      {!!bookings.length && (<><h4>Bookings</h4><table><thead><tr><th>Candidate</th><th>Slot</th><th>Email</th></tr></thead>
      <tbody>{bookings.map((b) => <tr key={b.candidate_id}><td>{b.candidate_id}</td><td>{b.slot}</td><td>{b.email_id}</td></tr>)}</tbody></table></>)}
    </div>
  );
}
