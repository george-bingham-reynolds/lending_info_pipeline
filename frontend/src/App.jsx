import { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const question = input.trim();
    setInput('');
    setError(null);
    
    // Add user question to messages
    const userMessage = { type: 'question', text: question };
    setMessages(prev => [...prev, userMessage]);
    
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add answer to messages
      const answerMessage = { type: 'answer', text: data.answer };
      setMessages(prev => [...prev, answerMessage]);
      
    } catch (err) {
      setError(`Unable to reach backend service. Please ensure the API server is running at http://localhost:8000. Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Lending Information Assistant</h1>
        <p className="subtitle">Commercial Real Estate Loan Query System</p>
      </header>

      <main className="chat-container">
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>Ask questions about commercial real estate loans.</p>
              <p className="hint">Example: "What was the net operating income for loan number MTN-10234?"</p>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-label">
                {message.type === 'question' ? 'Question' : 'Analysis'}
              </div>
              <div className="message-content">
                {message.text}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message answer loading-message">
              <div className="message-label">Analysis</div>
              <div className="message-content">
                <div className="loading-indicator">
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                  <span className="loading-text">Processing query and retrieving loan data...</span>
                </div>
              </div>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your question about a loan..."
            className="question-input"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="submit-button"
            disabled={isLoading || !input.trim()}
          >
            Submit Query
          </button>
        </form>
      </main>

      <footer className="app-footer">
        <p>Internal Tool • Underwriting Team • Data sourced from BigQuery</p>
      </footer>
    </div>
  );
}

export default App;
