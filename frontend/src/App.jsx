import React, { useState, useEffect } from 'react';
import QueryInput from './QueryInput';
import ChartRenderer from './ChartRenderer';
import DataTable from './DataTable';
import ResultsView from './ResultsView';
import { api } from '../services/api';
import './../styles/main.css';

const App = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (queryText) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.query(queryText);
      setResults(response);
      setHistory([{ query: queryText, timestamp: new Date(), ...response }, ...history]);
    } catch (err) {
      setError(err.message || 'Failed to process query');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Enterprise Text-to-SQL</h1>
        <div className="app-status">
          <span className="status-indicator">● Online</span>
        </div>
      </header>

      <main className="app-main">
        <section className="query-section">
          <QueryInput
            value={query}
            onChange={setQuery}
            onSubmit={handleSubmit}
            loading={loading}
            error={error}
          />
        </section>

        {results && (
          <section className="results-section">
            <ResultsView
              data={results.data}
              visualization={results.visualization}
              intent={results.intent}
              sql={results.sql}
            />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-info">
          <span>v1.0.0</span>
          <span>•</span>
          <span>Powered by Qwen2.5-Coder</span>
        </div>
      </footer>
    </div>
  );
};

export default App;