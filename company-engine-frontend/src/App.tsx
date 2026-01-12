import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Companies from './pages/Companies';
import CompanyDetail from './pages/CompanyDetail';
import EntityBrowser from './pages/EntityBrowser';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              SOCIAL INTELLIGENCE ENGINE
            </Link>
            <div className="nav-links">
              <Link to="/">Home</Link>
              <Link to="/companies">Companies</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/companies/:companyId" element={<CompanyDetail />} />
            <Route path="/companies/:companyId/entities" element={<EntityBrowser />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>Social Intelligence Engine API - Built with React and FastAPI</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
