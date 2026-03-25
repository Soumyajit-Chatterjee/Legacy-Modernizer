import { useState } from 'react'
import './index.css'

function App() {
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
      const response = await fetch('http://localhost:8000/api/modernize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          legacy_code: legacyCode,
          target_function: targetFunction,
          target_lang: targetLang
        })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to modernize code');
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
            <span className="pane-title">Source Input</span>
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
          
          <textarea 
            className="code-editor"
            value={legacyCode}
            onChange={(e) => setLegacyCode(e.target.value)}
            spellCheck="false"
          />
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
