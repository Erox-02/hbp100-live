function LoadingSpinner() {
  return (
    <div className="mt-12 flex flex-col items-center justify-center animate-fade-in">
      <div className="relative w-20 h-20">
        {/* Outer ring */}
        <div className="absolute inset-0 border-4 border-gray-800 rounded-full"></div>
        
        {/* Spinning ring */}
        <div className="absolute inset-0 border-4 border-transparent border-t-gray-500 border-r-gray-600 rounded-full animate-spin"></div>
        
        {/* Inner shield icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
          </svg>
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <p className="text-lg font-semibold text-gray-300">Processing Pipeline</p>
        <p className="text-sm text-gray-500 mt-1">Sanitizing and sending to LLM...</p>
      </div>
      
      {/* Pipeline stages indicator */}
      <div className="mt-6 flex items-center space-x-4">
        {['Sanitizing', 'Masking', 'Sending to LLM', 'Restoring'].map((stage, i) => (
          <div key={i} className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: `${i * 0.5}s` }}></div>
            <span className="text-xs text-gray-500">{stage}</span>
            {i < 3 && (
              <svg className="w-4 h-4 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
              </svg>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default LoadingSpinner
