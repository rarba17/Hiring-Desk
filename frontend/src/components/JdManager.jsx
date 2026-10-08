import { useEffect, useState } from 'react';
import { api } from '../api.js';

export function JdManager() {
  const [role, setRole] = useState('software engineer');
  const [text, setText] = useState('Role: Software Engineer (Backend, AI)\nRequirements: Python, FastAPI, LangChain, LLM apps, AWS, Postgres, pytest.\nMust have: 3+ years building APIs.');
  const [list, setList] = useState([]);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    setBusy(true); setMsg('');
    try {
      const j = await api.jds();
      setList(j.jds || []);
      setMsg(`loaded ${(j.jds || []).length} JD(s)`);
    } catch (e) { setMsg(`list failed: ${e.message || e}`); }
    finally { setBusy(false); }
  };
  useEffect(() => { refresh(); }, []);
  const save = async () => {
    setBusy(true); setMsg('');
    try {
      const j = await api.saveJD(role, text);
      setMsg(`saved ${j.key} (${j.chars} chars)`);
      const l = await api.jds();
      setList(l.jds || []);
    } catch (e) { setMsg(`save failed: ${e.message || e}`); }
    finally { setBusy(false); }
  };
  return (
    <div className="card">
      <h3>3 · Job descriptions</h3>
      <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="role" />
      <textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} />
      <div><button type="button" onClick={save} disabled={busy}>{busy ? 'Working…' : 'Save JD'}</button><button type="button" className="ghost" onClick={refresh} disabled={busy}>{busy ? 'Loading…' : 'List'}</button></div>
      {msg && <p><small>{msg}</small></p>}
      <p><small>{list.join(' · ') || 'no JDs'}</small></p>
    </div>
  );
}
