const TICKS = ['Python', 'FastAPI', 'LangChain', 'LLM apps', 'AWS', 'Postgres', 'pytest', 'Docker', 'React', 'Top 5', 'No double-books', 'ATS updated'];

export function Landing() {
  return (
    <div className="app">
      <header className="masthead">
        <div className="masthead-row">
          <div>
            <span className="folder-tab">Interview dossier</span>
            <h1>Hiring desk</h1>
          </div>
          <a className="btn-ink" href="#/console">Open the console</a>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="lede">Autonomous interview scheduling with receipts.</p>
          <p className="hero-sub">
            Type one sentence. The worker screens every resume against the job description,
            books a conflict-free panel slot for each finalist, sends the invites, updates
            the tracker — then proves all of it.
          </p>
          <div className="hero-cta">
            <a className="btn-ink" href="#/console">Open the hiring desk</a>
            <a className="btn-paper" href="#how">How it runs</a>
          </div>
        </div>
        <div className="hero-stage" aria-hidden="true">
          <div className="slip s1"><b>Anna Patel</b><span>92.4 · FastAPI · LLM</span></div>
          <div className="slip s2"><b>Grace Liu</b><span>88.1 · Platform · AWS</span></div>
          <div className="slip s3"><b>Erin Fox</b><span>84.7 · LangChain · OpenAI</span></div>
          <div className="demo-sheet">
            <p className="demo-line">Top 5 · software engineer</p>
            <p className="demo-line dim">slot 2026-10-12T14:00 · panel alice, bob</p>
            <span className="stamp done loop">Scheduled</span>
          </div>
        </div>
      </section>

      <div className="ticker" aria-hidden="true">
        <div className="ticker-track">
          {[0, 1].map((k) => (
            <span key={k} className="ticker-run">
              {TICKS.map((t) => <em key={`${k}-${t}`}>{t}</em>)}
            </span>
          ))}
        </div>
      </div>

      <section id="how" className="card">
        <h3>How a run works</h3>
        <ol className="runway">
          <li><b>State the goal.</b> “Schedule interviews for the top 5 candidates for the software engineer role.” The planner extracts role, headcount, panel and duration.</li>
          <li><b>Resumes meet the JD.</b> Every resume is scored 0–100 against that role's job description and ranked. Weak shortlists pause for your sign-off.</li>
          <li><b>The calendar gets solved.</b> First free slot where the whole panel is open — one per finalist, invites sent, tracker flipped to interview scheduled.</li>
          <li><b>Proof, not promises.</b> A checker verifies headcount, no double-books, tracker stages and email receipts before calling it done.</li>
        </ol>
      </section>

      <div className="grid">
        <section className="card">
          <h3>Start it locally</h3>
          <pre className="trace">cp .env.example .env   # add OPENAI_API_KEY, or rule scoring runs
pip install -r requirements.txt
uvicorn app.api.main:app --reload   # backend :8000</pre>
          <pre className="trace">npm install --prefix frontend
npm run dev --prefix frontend       # console :5173</pre>
          <p><a className="btn-ink" href="#/console">Proceed to the product</a></p>
        </section>
        <section className="card">
          <h3>Field notes</h3>
          <ul className="notes">
            <li>Upload a PDF resume, re-run, watch the ranking move.</li>
            <li>Set SCORE_THRESHOLD=95 to force the sign-off gate.</li>
            <li>Block a panel slot in calendars/ to watch it re-plan.</li>
            <li>Every run appends its trace to trace.jsonl — keep it as evidence.</li>
          </ul>
        </section>
      </div>

      <p className="desk-note">Built as an intern-prototype autonomous worker: FastAPI + LangGraph + OpenAI, one container, mock inbox and calendars, deterministic verification.</p>
    </div>
  );
}
