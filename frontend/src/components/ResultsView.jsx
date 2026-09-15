import React, { useState } from 'react';
import ChartRenderer from './ChartRenderer';
import DataTable from './DataTable';

const ResultsView = ({ data, visualization, intent, sql }) => {
  const [activeTab, setActiveTab] = useState('chart');
  
  if (!data || data.length === 0) {
    return (
      <div className="results-empty">
        <p>No results found.</p>
      </div>
    );
  }
  
  return (
    <div className="results-view">
      <div className="results-header">
        <div className="results-tabs">
          <button 
            className={`tab ${activeTab === 'chart' ? 'active' : ''}`}
            onClick={() => setActiveTab('chart')}
          >
            Chart
          </button>
          <button 
            className={`tab ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            Table
          </button>
          <button 
            className={`tab ${activeTab === 'sql' ? 'active' : ''}`}
            onClick={() => setActiveTab('sql')}
          >
            SQL
          </button>
        </div>
        <div className="results-info">
          <span>{data.length} rows</span>
        </div>
      </div>
      
      <div className="results-content">
        {activeTab === 'chart' && visualization && (
          <ChartRenderer 
            spec={visualization.spec} 
            data={data}
          />
        )}
        {activeTab === 'table' && (
          <DataTable data={data} />
        )}
        {activeTab === 'sql' && (
          <div className="sql-display">
            <pre className="sql-code">{sql}</pre>
            {intent && (
              <div className="intent-info">
                <h4>Intent</h4>
                <pre>{JSON.stringify(intent, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsView;