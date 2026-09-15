import React, { useState, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

const DataTable = ({ data }) => {
  const [columnDefs] = useState(() => {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]).map(key => ({
      field: key,
      headerName: key.replace(/_/g, ' ').toUpperCase(),
      sortable: true,
      filter: true,
      resizable: true,
      width: 150
    }));
  });
  
  const rowData = useMemo(() => data || [], [data]);
  
  return (
    <div className="data-table-container ag-theme-alpine" style={{ height: '500px', width: '100%' }}>
      <AgGridReact
        columnDefs={columnDefs}
        rowData={rowData}
        pagination={true}
        paginationPageSize={50}
        paginationPageSizeSelector={[10, 25, 50, 100]}
        enableCellTextSelection={true}
        ensureDomOrder={true}
        suppressRowClickSelection={true}
        rowSelection={null}
      />
    </div>
  );
};

export default DataTable;