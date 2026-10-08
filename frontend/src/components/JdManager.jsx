import { useEffect, useState } from 'react';
import { api } from '../api.js';

export function JdManager() {
  const [role, setRole] = useState('software engineer');
  const [text, setText] = useState('Role: Software Engineer (Backend, AI)\nRequirements: Python, FastAPI, LangChain, LLM apps, AWS, Postgres, pytest.\nMust have: 3+ years building APIs.');
  const [list, setList] = useState([]);
  const [msg, setMsg] = useState('');
  const refresh = async () => setList((await api.jds()).jds || []);
  useEffect(() => { refresh(); }, []);
  const save = async () => {
    const j = await api.saveJD(role, text);
    setMsg(`saved ${j.key} (${j.chars} chars)`);
    refresh();
  };
  return (
    <div className="card">
      <h3>3 · Job descriptions</h3>
      <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="role" />
      <textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} />
      <div><button onClick={save}>Save JD</button><button className="ghost" onClick={refresh}>List</button></div>
      {msg && <p>{msg}</p>}
      <p><small>{list.join(' · ') || 'no JDs'}</small></p>
    </div>
  );
}
