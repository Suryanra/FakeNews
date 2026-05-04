import { useState } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldAlert, FileText, Search, Loader2, FilePlus } from 'lucide-react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  const [addNewsText, setAddNewsText] = useState('');
  const [addNewsTitle, setAddNewsTitle] = useState('');
  const [addNewsLoading, setAddNewsLoading] = useState(false);
  const [addNewsSuccess, setAddNewsSuccess] = useState('');
  const [addNewsError, setAddNewsError] = useState('');

  const [activeTab, setActiveTab] = useState('fact-checker');

  // Admin Login State
  const [isAdmin, setIsAdmin] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [authToken, setAuthToken] = useState('');

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('http://localhost:8000/api/analyze', { text: query });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError('An error occurred while analyzing the text. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddNews = async (e) => {
    e.preventDefault();
    if (!addNewsText.trim() || !addNewsTitle.trim()) return;

    setAddNewsLoading(true);
    setAddNewsError('');
    setAddNewsSuccess('');

    try {
      const response = await axios.post(
        'http://localhost:8000/api/add-news', 
        { text: addNewsText, title: addNewsTitle },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      setAddNewsSuccess(response.data.message || 'News added successfully!');
      setAddNewsText('');
      setAddNewsTitle('');
    } catch (err) {
      console.error(err);
      setAddNewsError('An error occurred while adding the news. Please try again.');
    } finally {
      setAddNewsLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      const response = await axios.post('http://localhost:8000/api/login', {
        username: loginUsername,
        password: loginPassword
      });
      setAuthToken(response.data.token);
      setIsAdmin(true);
      setLoginUsername('');
      setLoginPassword('');
    } catch (err) {
      setLoginError('Invalid username or password');
    }
  };

  const handleLogout = () => {
    setIsAdmin(false);
    setAuthToken('');
  };

  const getAssessmentStyle = (assessment) => {
    const lower = assessment.toLowerCase();
    if (lower.startsWith('true') || lower.includes('likely true')) return 'assessment-true';
    if (lower.startsWith('fake') || lower.includes('likely fake')) return 'assessment-fake';
    return 'assessment-neutral';
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <ShieldCheck size={32} color="var(--accent-color)" />
          <h1>Veritas AI</h1>
        </div>
        <div className="header-actions">
          {isAdmin ? (
            <button type="button" className="admin-btn" onClick={handleLogout}>Sign out</button>
          ) : (
            <button
              type="button"
              className="admin-btn"
              onClick={() => setActiveTab('add-news')}
            >
              Sign in
            </button>
          )}
        </div>
      </header>

      <nav className="tab-nav glass-panel" aria-label="Main sections">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'fact-checker'}
          className={`tab-btn ${activeTab === 'fact-checker' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('fact-checker')}
        >
          <Search size={18} aria-hidden="true" />
          Fact-checker
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'add-news'}
          className={`tab-btn ${activeTab === 'add-news' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('add-news')}
        >
          <FilePlus size={18} aria-hidden="true" />
          Add news
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'fact-checker' && (
          <>
            <div className="glass-panel input-section animate-fade-in">
              <h2>Analyze News</h2>
              <p className="tab-lead">Paste a headline or article to compare against the knowledge base.</p>
              <form onSubmit={handleAnalyze}>
                <div className="input-wrapper">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Paste an article or headline here..."
                    rows={5}
                    className="news-input"
                  />
                </div>
                <button
                  type="submit"
                  className="analyze-btn"
                  disabled={loading || !query.trim()}
                >
                  {loading ? <Loader2 className="spinner" size={20} /> : <Search size={20} />}
                  <span>{loading ? 'Analyzing...' : 'Analyze Text'}</span>
                </button>
              </form>
              {error && <div className="error-msg">{error}</div>}
            </div>

            {result && (
              <div className="results-container animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div className={`glass-panel result-card ${getAssessmentStyle(result.assessment)}`}>
                  <div className="result-header">
                    {getAssessmentStyle(result.assessment) === 'assessment-true' ? (
                      <ShieldCheck size={28} />
                    ) : (
                      <ShieldAlert size={28} />
                    )}
                    <h3>AI Assessment</h3>
                  </div>
                  <p className="assessment-text">{result.assessment}</p>
                </div>

                {result.sources && result.sources.length > 0 && (
                  <div className="glass-panel sources-card">
                    <h3><FileText size={20} /> Retrieved Facts (RAG Sources)</h3>
                    <div className="sources-list">
                      {result.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <p className="source-content">&quot;{source.content}&quot;</p>
                          {source.metadata && Object.keys(source.metadata).length > 0 && (
                            <div className="source-meta">
                              {Object.entries(source.metadata).map(([k, v]) => (
                                <span key={k} className="meta-badge">{k}: {v}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {activeTab === 'add-news' && (
          <div className="animate-fade-in">
            {!isAdmin && (
              <div className="glass-panel input-section add-news-login">
                <h2>Admin sign-in</h2>
                <p className="tab-lead">Sign in to add verified facts to the knowledge base.</p>
                <form onSubmit={handleLogin} className="login-form-row">
                  <input
                    type="text"
                    placeholder="Username"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    className="news-input login-field"
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="news-input login-field"
                  />
                  <button type="submit" className="analyze-btn login-submit">
                    Sign in
                  </button>
                </form>
                {loginError && <div className="error-msg">{loginError}</div>}
              </div>
            )}

            {isAdmin && (
              <div className="glass-panel input-section">
                <h2>Add to knowledge base</h2>
                <p className="tab-lead">Submit verified text so it can be retrieved during fact-checking.</p>
                <form onSubmit={handleAddNews}>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      value={addNewsTitle}
                      onChange={(e) => setAddNewsTitle(e.target.value)}
                      placeholder="Title or subject"
                      className="news-input"
                    />
                  </div>
                  <div className="input-wrapper">
                    <textarea
                      value={addNewsText}
                      onChange={(e) => setAddNewsText(e.target.value)}
                      placeholder="Paste the verified facts or article text here..."
                      rows={5}
                      className="news-input"
                    />
                  </div>
                  <button
                    type="submit"
                    className="analyze-btn add-news-submit"
                    disabled={addNewsLoading || !addNewsText.trim() || !addNewsTitle.trim()}
                  >
                    {addNewsLoading ? <Loader2 className="spinner" size={20} /> : <FilePlus size={20} />}
                    <span>{addNewsLoading ? 'Adding…' : 'Add to knowledge base'}</span>
                  </button>
                </form>
                {addNewsError && <div className="error-msg">{addNewsError}</div>}
                {addNewsSuccess && <div className="success-msg">{addNewsSuccess}</div>}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
