import { useState } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldAlert, FileText, Search, Loader2 } from 'lucide-react';
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
      const response = await axios.post('http://localhost:8000/api/add-news', { 
        text: addNewsText, 
        title: addNewsTitle 
      });
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
        <p>RAG-Powered Fake News Detection</p>
      </header>

      <main className="main-content">
        <div className="glass-panel input-section animate-fade-in">
          <h2>Analyze News</h2>
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

        <div className="glass-panel input-section animate-fade-in" style={{ marginTop: '2rem' }}>
          <h2>Add to Knowledge Base</h2>
          <p style={{marginBottom: '1rem', color: 'var(--text-secondary)'}}>Submit verified news facts so they can be used for future analysis.</p>
          <form onSubmit={handleAddNews}>
            <div className="input-wrapper" style={{ marginBottom: '1rem' }}>
              <input 
                type="text"
                value={addNewsTitle}
                onChange={(e) => setAddNewsTitle(e.target.value)}
                placeholder="News Title / Subject"
                className="news-input"
                style={{ padding: '0.8rem', borderBottom: '1px solid var(--glass-border)' }}
              />
            </div>
            <div className="input-wrapper">
              <textarea 
                value={addNewsText}
                onChange={(e) => setAddNewsText(e.target.value)}
                placeholder="Paste the verified facts or article text here..."
                rows={4}
                className="news-input"
              />
            </div>
            <button 
              type="submit" 
              className="analyze-btn" 
              style={{ background: 'var(--success-color)' }}
              disabled={addNewsLoading || !addNewsText.trim() || !addNewsTitle.trim()}
            >
              {addNewsLoading ? <Loader2 className="spinner" size={20} /> : <ShieldCheck size={20} />}
              <span>{addNewsLoading ? 'Adding...' : 'Add News'}</span>
            </button>
          </form>
          {addNewsError && <div className="error-msg">{addNewsError}</div>}
          {addNewsSuccess && <div className="success-msg" style={{color: 'var(--success-color)', marginTop: '1rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px'}}>{addNewsSuccess}</div>}
        </div>

        {result && (
          <div className="results-container animate-fade-in" style={{ animationDelay: '0.2s' }}>
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
                      <p className="source-content">"{source.content}"</p>
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
      </main>
    </div>
  );
}

export default App;
