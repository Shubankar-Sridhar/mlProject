import React, { useState } from 'react';

const QueryInput = ({ value, onChange, onSubmit, loading, error }) => {
  const [inputValue, setInputValue] = useState(value);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !loading) {
      onSubmit(inputValue);
    }
  };
  
  const handleChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    if (onChange) {
      onChange(newValue);
    }
  };
  
  return (
    <div className="query-input">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <input
            type="text"
            value={inputValue}
            onChange={handleChange}
            placeholder="Ask a question about your data..."
            disabled={loading}
            className="query-field"
          />
          <button 
            type="submit" 
            disabled={!inputValue.trim() || loading}
            className="submit-button"
          >
            {loading ? 'Processing...' : 'Ask'}
          </button>
        </div>
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
        {loading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Generating query...</span>
          </div>
        )}
      </form>
    </div>
  );
};

export default QueryInput;