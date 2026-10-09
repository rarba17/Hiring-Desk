// VITE_API_URL points at the backend in production (e.g. https://hiring-api.onrender.com).
// Empty in local dev, where vite.config.js proxies to :8000.
const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function req(path, opts = {}) {
  try {
    return await once(path, opts);
  } catch (e) {
    // Cold-start cover: Render free tier can take ~60s to wake. Retry idempotent
    // reads once after a wait; writes fail fast so runs are never duplicated.
    const safe = !opts.method || opts.method === 'GET';
    if (safe && e instanceof TypeError) {
      await new Promise((r) => setTimeout(r, 45000));
      return once(path, opts);
    }
    throw e;
  }
}

async function once(path, opts = {}) {
  const r = await fetch(`${BASE}${path}`, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export const api = {
  runTask(goal) {
    return req('/hiring/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ goal }) });
  },
  approve(tid, decision = 'approved') {
    return req(`/hiring/tasks/${tid}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }) });
  },
  ats(role = '') {
    const q = role ? `?role=${encodeURIComponent(role)}` : '';
    return req(`/ats/candidates${q}`);
  },
  jds() {
    return req('/jds');
  },
  saveJD(role, text) {
    return req('/jds', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role, text }) });
  },
  jdView(role) {
    return req(`/jds/${encodeURIComponent(role)}`);
  },
  jdDelete(role) {
    return req(`/jds/${encodeURIComponent(role)}`, { method: 'DELETE' });
  },
  uploadResume(file) {
    const fd = new FormData();
    fd.append('file', file);
    return req('/resumes/upload', { method: 'POST', body: fd });
  },
  health() {
    return req('/health');
  }
};
