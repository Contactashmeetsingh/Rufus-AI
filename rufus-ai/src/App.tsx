import './App.css'

function App() {
  return (
    <div id="root">
      <header className="site-header">
        <div className="brand">
          <img src="/vite.svg" className="logo" alt="Rufus AI logo" />
          <div>
            <h1>Rufus AI</h1>
            <p className="tagline">A helper for UC Merced students, parents, and faculty.</p>
          </div>
        </div>

        <nav className="site-nav" aria-label="Primary">
          <a href="#students">Students</a>
          <a href="#parents">Parents</a>
          <a href="#faculty">Faculty/Staff</a>
        </nav>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-heading">
          <h2 id="hero-heading">Answers and help for everything UC Merced — registration, campus life, and resources.</h2>

          <div className="search">
            <input type="text" placeholder="e.g., How do I register for CS 101?" aria-label="Ask Rufus" />
            <button className="primary">Ask Rufus</button>
          </div>

          <div className="cta-row">
            <button className="primary">Get Started</button>
            <a className="learn" href="#learn-more">Learn more</a>
          </div>
        </section>

        <section className="features" id="learn-more">
          <article>
            <h3>Course registration</h3>
            <p>Step-by-step help with enrollment, deadlines, and prerequisites.</p>
          </article>

          <article>
            <h3>Campus information</h3>
            <p>Find maps, offices, events, and student services across campus.</p>
          </article>

          <article>
            <h3>Parents & faculty</h3>
            <p>Resources tailored to support students from families and staff.</p>
          </article>
        </section>

        <section className="about" id="students">
          <h3>Who it's for</h3>
          <p>
            Rufus AI is a prototype assistant for UC Merced students, parents, and faculty — a quick way to
            find answers about courses, registration, campus life, and support services.
          </p>
        </section>
      </main>

      <footer className="site-footer">
        <p>Built for UC Merced — prototype. Contact: rufus@example.edu</p>
      </footer>
    </div>
  )
}

export default App
