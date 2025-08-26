import React, { useState } from 'react';

const ExportToolsWidget = ({ data, config, onRefresh, refreshing }) => {
  const [exporting, setExporting] = useState(false);
  const formats = config?.formats || ['csv', 'xlsx', 'pdf'];

  const handleExport = async (format) => {
    setExporting(true);
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert(`Export to ${format.toUpperCase()} completed!`);
    } finally {
      setExporting(false);
    }
  };

  const getFormatIcon = (format) => {
    switch (format) {
      case 'csv': return '📈';
      case 'xlsx': return '📉';
      case 'pdf': return '📝';
      default: return '📄';
    }
  };

  const getFormatLabel = (format) => {
    switch (format) {
      case 'csv': return 'CSV Spreadsheet';
      case 'xlsx': return 'Excel Workbook';
      case 'pdf': return 'PDF Report';
      default: return format.toUpperCase();
    }
  };

  return (
    <div className="h-full">
      <h3 className="text-sm font-medium text-gray-900 mb-4">
        Export Data
      </h3>

      <div className="space-y-3">
        {formats.map((format) => (
          <button
            key={format}
            onClick={() => handleExport(format)}
            disabled={exporting}
            className="w-full flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow disabled:opacity-50"
          >
            <div className="flex items-center space-x-3">
              <span className="text-lg">{getFormatIcon(format)}</span>
              <div className="text-left">
                <div className="text-sm font-medium text-gray-900">
                  {getFormatLabel(format)}
                </div>
                <div className="text-xs text-gray-500">
                  Download customer data as {format.toUpperCase()}
                </div>
              </div>
            </div>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
        ))}
      </div>

      {exporting && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <svg className="animate-spin h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm text-blue-800">Preparing export...</span>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        <p>Exports include all customer data visible to your account.</p>
        <p className="mt-1">Large datasets may take a few minutes to process.</p>
      </div>
    </div>
  );
};

export default ExportToolsWidget;