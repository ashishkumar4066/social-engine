import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Companies from './pages/Companies';
import CompanyDetail from './pages/CompanyDetail';
import EntityBrowser from './pages/EntityBrowser';
import './App.css';

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to ||
    (to === '/companies' && location.pathname.startsWith('/companies/'));

  return (
    <Link to={to} className={isActive ? 'active' : ''}>
      {children}
    </Link>
  );
}

function Navigation() {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <div className="nav-logo-icon">S</div>
          <span className="nav-logo-text">
            Social<span>Intel</span>
          </span>
        </Link>
        <div className="nav-links">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/companies">Companies</NavLink>
        </div>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-brand">
          <div className="footer-brand-icon">S</div>
          <span className="footer-brand-text">Social Intelligence Engine</span>
        </div>
        <p>Discover insights from Reddit conversations about any company</p>
        <div className="footer-links">
          <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="#" onClick={(e) => e.preventDefault()}>Documentation</a>
          <a href="#" onClick={(e) => e.preventDefault()}>API</a>
        </div>
      </div>
    </footer>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/companies/:companyId" element={<CompanyDetail />} />
            <Route path="/companies/:companyId/entities" element={<EntityBrowser />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
