function MetadataViewer({ metadata }) {
  if (!metadata || Object.keys(metadata).length === 0) {
    return (
      <div className="bg-gray-950 rounded-lg border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Metadata Vault</h3>
        <p className="text-gray-500 text-sm">No PII detected - vault is empty</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-950 rounded-lg border border-gray-800 p-6 card-glow border-l-4 border-l-gray-600">
      <div className="flex items-center space-x-3 mb-4">
        <h3 className="text-lg font-semibold text-gray-200">Metadata Vault</h3>
        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-800 text-gray-400">
          {Object.keys(metadata).length} entries
        </span>
      </div>
      
      <div className="space-y-3">
        {Object.entries(metadata).map(([placeholder, value], index) => (
          <div key={index} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-gray-400 bg-gray-800 px-2 py-1 rounded">
                {placeholder}
              </span>
              <span className="text-xs text-gray-600">
                Placeholder
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4 text-gray-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
              </svg>
              <span className="font-mono text-sm text-gray-300 break-all">
                {value}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
        <p className="text-xs text-gray-500 flex items-center">
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
          </svg>
          These values never leave your device
        </p>
      </div>
    </div>
  )
}

export default MetadataViewer
