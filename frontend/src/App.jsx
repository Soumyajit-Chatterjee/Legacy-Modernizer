import { useState } from 'react'
import './index.css'

function App() {
  const [inputType, setInputType] = useState('code'); // 'code' or 'github'
  const [githubUrl, setGithubUrl] = useState('');
  const [legacyCode, setLegacyCode] = useState('// Paste Legacy Java Code Here\n');
  const [targetFunction, setTargetFunction] = useState('');
  const [targetLang, setTargetLang] = useState('python');
  
  const [modernizedCode, setModernizedCode] = useState('');
  const [unitTests, setUnitTests] = useState('');
  const [activeTab, setActiveTab] = useState('code'); // 'code' or 'tests'
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleModernize = async () => {
    if (!targetFunction) {
      setError('Please specify a target function.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      let endpoint = 'http://localhost:8000/api/modernize';
      let payload = {
        target_function: targetFunction,
        target_lang: targetLang
      };
      
      if (inputType === 'github') {
        if (!githubUrl) {
          setError('Please specify a GitHub URL.');
          setIsLoading(false);
          return;
        }
        endpoint = 'http://localhost:8000/api/modernize/github';
        payload.github_url = githubUrl;
      } else {
        payload.legacy_code = legacyCode;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        let errData;
        try { errData = await response.json(); } catch(e) {}
        throw new Error(errData?.detail || 'Failed to modernize code');
      }
      
      const data = await response.json();
      setModernizedCode(data.modernized_code || 'No code returned.');
      setUnitTests(data.unit_tests || 'No tests returned.');
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>Legacy Modernizer</h1>
        <div className="header-status">
          <div className="status-dot"></div>
          Engine Ready
        </div>
      </header>

      <div className="workspace">
        {/* Left Pane - Input */}
        <div className="pane">
          <div className="pane-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span className="pane-title">Source Input</span>
              <div style={{ display: 'flex', background: 'var(--surface-color)', borderRadius: '4px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
                <button 
                  style={{ padding: '4px 12px', fontSize: '0.75rem', cursor: 'pointer', background: inputType === 'code' ? 'var(--text-primary)' : 'transparent', color: inputType === 'code' ? 'var(--surface-color)' : 'var(--text-secondary)', border: 'none', fontWeight: 600 }}
                  onClick={() => setInputType('code')}
                >RAW CODE</button>
                <button 
                  style={{ padding: '4px 12px', fontSize: '0.75rem', cursor: 'pointer', background: inputType === 'github' ? 'var(--text-primary)' : 'transparent', color: inputType === 'github' ? 'var(--surface-color)' : 'var(--text-secondary)', border: 'none', fontWeight: 600 }}
                  onClick={() => setInputType('github')}
                >GITHUB URL</button>
              </div>
            </div>
            <div className="controls-group">
              <input 
                type="text" 
                placeholder="Target Function Name" 
                value={targetFunction}
                onChange={(e) => setTargetFunction(e.target.value)}
              />
              <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                <option value="python">Python</option>
                <option value="go">Go</option>
              </select>
              <button 
                className="primary-btn" 
                onClick={handleModernize}
                disabled={isLoading}
              >
                {isLoading ? 'Processing...' : 'Modernize'}
              </button>
            </div>
          </div>
          
          {error && (
             <div style={{ color: '#dc2626', padding: '1rem 1.5rem', fontSize: '0.875rem', borderBottom: '1px solid var(--border-color)' }}>
               Error: {error}
             </div>
          )}
          
          {inputType === 'code' ? (
            <textarea 
              className="code-editor"
              value={legacyCode}
              onChange={(e) => setLegacyCode(e.target.value)}
              spellCheck="false"
            />
          ) : (
            <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>Ingest from GitHub</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: 0, lineHeight: 1.5 }}>
                Enter the full URL of a public GitHub repository. The backend will intelligently clone the repository, map cross-file dependencies via BFS, and optimize the context to guarantee zero LLM hallucinations.
              </p>
              <input 
                type="text" 
                placeholder="https://github.com/user/repo" 
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                style={{ 
                  width: '100%', 
                  padding: '0.875rem', 
                  background: 'var(--bg-secondary)', 
                  border: '1px solid var(--border-color)', 
                  color: 'var(--text-primary)',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          )}
        </div>

        {/* Right Pane - Output */}
        <div className="pane">
          <div className="pane-header">
            <div className="tabs">
              <button 
                className={`tab ${activeTab === 'code' ? 'active' : ''}`}
                onClick={() => setActiveTab('code')}
              >
                MODERNIZED CODE
              </button>
              <button 
                className={`tab ${activeTab === 'tests' ? 'active' : ''}`}
                onClick={() => setActiveTab('tests')}
              >
                UNIT TESTS
              </button>
            </div>
          </div>
          
          {modernizedCode || unitTests ? (
             <pre className="code-output">
               {activeTab === 'code' ? modernizedCode : unitTests}
             </pre>
          ) : (
            <div className="empty-state">
               Output will appear here...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
