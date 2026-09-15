import React, { useRef, useEffect, useState } from 'react';
import { VegaLite } from 'react-vega';

const ChartRenderer = ({ spec, data, onChartClick }) => {
  const [chartSpec, setChartSpec] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (spec && data) {
      const mergedSpec = {
        ...spec,
        data: { values: data },
        width: 'container',
        height: 400
      };
      setChartSpec(mergedSpec);
    }
  }, [spec, data]);

  if (!chartSpec) {
    return (
      <div className="chart-placeholder">
        <p>No chart available</p>
      </div>
    );
  }

  return (
    <div className="chart-container" ref={containerRef}>
      <VegaLite
        spec={chartSpec}
        actions={false}
        renderer="svg"
        onNewView={(view) => {
          if (onChartClick) {
            view.addEventListener('click', (event, item) => {
              onChartClick(item);
            });
          }
        }}
      />
    </div>
  );
};

export default ChartRenderer;