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
  const normKey = (s) => (s || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const stem = (f) => f.replace(/\.(txt|md)$/i, '');
  const view = async (f) => {
    setBusy(true); setMsg('');
    try {
      const j = await api.jdView(stem(f));
      setRole(stem(f).replace(/_/g, ' '));
      setText(j.text);
      setMsg(`viewing ${f} (${j.text.length} chars)`);
    } catch (e) { setMsg(`view failed: ${e.message || e}`); }
    finally { setBusy(false); }
  };
  const remove = async (f) => {
    if (!window.confirm(`Delete ${f}? Future runs will fall back to another JD.`)) return;
    setBusy(true); setMsg('');
    try {
      await api.jdDelete(stem(f));
      const l = await api.jds();
      setList(l.jds || []);
      if (normKey(stem(f)) === normKey(role)) setText('');
      setMsg(`deleted ${f}`);
    } catch (e) { setMsg(`delete failed: ${e.message || e}`); }
    finally { setBusy(false); }
  };
  return (
    <div className="card">
      <h3>3 · Job descriptions</h3>
      <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="role" />
      <textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} />
      <div><button type="button" onClick={save} disabled={busy}>{busy ? 'Working…' : 'Save JD'}</button><button type="button" className="ghost" onClick={refresh} disabled={busy}>{busy ? 'Loading…' : 'List'}</button></div>
      {msg && <p><small>{msg}</small></p>}
      {list.length ? (
        <table><tbody>{list.map((f) => (
          <tr key={f}><td><small>{stem(f).replace(/_/g, ' ')}</small><br /><small style={{ color: '#93a4bb' }}>{f}</small></td>
          <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
            <button type="button" className="ghost" onClick={() => view(f)} disabled={busy}>View</button>{' '}
            <button type="button" className="ghost" onClick={() => remove(f)} disabled={busy}>Delete</button>
          </td></tr>
        ))}</tbody></table>
      ) : <p><small>no JDs</small></p>}
    </div>
  );
}
