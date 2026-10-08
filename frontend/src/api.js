export const api = {
  async runTask(goal) {
    const r = await fetch('/hiring/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ goal }) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async approve(tid, decision = 'approved') {
    const r = await fetch(`/hiring/tasks/${tid}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async ats(role = '') {
    const q = role ? `?role=${encodeURIComponent(role)}` : '';
    return (await fetch(`/ats/candidates${q}`)).json();
  },
  async jds() {
    const r = await fetch('/jds');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async saveJD(role, text) {
    const r = await fetch('/jds', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role, text }) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async uploadResume(file) {
    const fd = new FormData();
    fd.append('file', file);
    const r = await fetch('/resumes/upload', { method: 'POST', body: fd });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async health() { return (await fetch('/health')).json(); }
};
