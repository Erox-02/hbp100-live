import { useState } from 'react'

function ResultCard({ title, data, type = 'original', fullWidth = false }) {
  const [copied, setCopied] = useState(false)

  const getTypeStyles = () => {
    switch (type) {
      case 'original':
        return 'border-l-4 border-l-gray-500'
      case 'masked':
        return 'border-l-4 border-l-gray-600'
      case 'llm':
        return 'border-l-4 border-l-gray-600'
      case 'restored':
        return 'border-l-4 border-l-gray-500'
      default:
        return ''
    }
  }

  const getTypeBadge = () => {
    switch (type) {
      case 'original':
        return { color: 'bg-gray-700/50 text-gray-400', label: 'Original' }
      case 'masked':
        return { color: 'bg-gray-700/50 text-gray-400', label: 'Masked' }
      case 'llm':
        return { color: 'bg-gray-700/50 text-gray-400', label: 'LLM Response' }
      case 'restored':
        return { color: 'bg-gray-700/50 text-gray-400', label: 'Restored' }
      default:
        return { color: '', label: '' }
    }
  }

  const badge = getTypeBadge()

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(data)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={`bg-gray-950 rounded-lg border border-gray-800 card-glow ${getTypeStyles()} ${fullWidth ? 'col-span-full' : ''}`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-200">{title}</h3>
            {badge.label && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
                {badge.label}
              </span>
            )}
          </div>
          
          <button
            onClick={copyToClipboard}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors group"
            title="Copy to clipboard"
          >
            {copied ? (
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-gray-600 group-hover:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
              </svg>
            )}
          </button>
        </div>
        
        <div className="code-block">
          <pre className="whitespace-pre-wrap break-words text-gray-300">
            {data || 'No data available'}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default ResultCard
