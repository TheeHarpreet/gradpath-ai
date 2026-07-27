import "./App.css";

const workflowStages = [
  {
    number: "01",
    title: "Provide evidence",
    description:
      "Add a redacted CV, job description, and optional project evidence.",
  },
  {
    number: "02",
    title: "Analyse requirements",
    description: "Separate essential, desirable, and unclear requirements.",
  },
  {
    number: "03",
    title: "Verify alignment",
    description: "Map every suggested claim to candidate-controlled evidence.",
  },
  {
    number: "04",
    title: "Review changes",
    description: "Accept, edit, or reject each important CV change.",
  },
];

function App() {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <a className="brand" href="/" aria-label="GradPath AI home">
          <span className="brand-mark" aria-hidden="true">
            GP
          </span>
          <span>GradPath AI</span>
        </a>
        <span className="phase-badge">Architecture foundation</span>
      </header>

      <main id="main-content">
        <section className="hero" aria-labelledby="hero-title">
          <p className="eyebrow">Evidence-grounded CV alignment</p>
          <h1 id="hero-title">Tailor the evidence, never invent the person.</h1>
          <p className="hero-copy">
            GradPath AI is being designed to analyse a candidate&apos;s real
            evidence against a job description, explain gaps, and prepare an
            aligned CV that remains under the candidate&apos;s control.
          </p>
          <div className="notice" role="status">
            <strong>Step 2:</strong> The architecture and engineering foundation
            are under construction. Document analysis is not available yet.
          </div>
        </section>

        <section className="workflow" aria-labelledby="workflow-title">
          <div className="section-heading">
            <p className="eyebrow">Planned workflow</p>
            <h2 id="workflow-title">
              A reviewable path from evidence to application
            </h2>
          </div>

          <ol className="workflow-grid">
            {workflowStages.map((stage) => (
              <li key={stage.number} className="workflow-card">
                <span className="step-number" aria-hidden="true">
                  {stage.number}
                </span>
                <h3>{stage.title}</h3>
                <p>{stage.description}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="principles" aria-labelledby="principles-title">
          <div>
            <p className="eyebrow">Non-negotiable controls</p>
            <h2 id="principles-title">
              Truth and user approval are product features.
            </h2>
          </div>
          <ul>
            <li>Unsupported requirements remain visible gaps.</li>
            <li>Important claims retain evidence citations.</li>
            <li>The candidate accepts, edits, or rejects changes.</li>
            <li>The candidate applies to the role independently.</li>
          </ul>
        </section>
      </main>

      <footer>
        <p>
          GradPath AI · Product definition complete · Architecture in progress
        </p>
      </footer>
    </div>
  );
}

export default App;
