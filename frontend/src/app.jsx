import { useState } from 'react'
import PromptInput from './components/PromptInput'
import ResultCard from './components/ResultCard'
import MetadataViewer from './components/MetadataViewer'
import LoadingSpinner from './components/LoadingSpinner'

const API_URL = import.meta.env.DEV 
  ? 'http://localhost:8000/'           
  : '/api/'                             

function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (prompt) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="border-b border-neutral-800 bg-neutral-900/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-neutral-800 rounded-lg flex items-center justify-center">
              <svg
                className="w-8 h-8 text-neutral-400"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
              </svg>
            </div>

            <div>
              <h1 className="text-3xl font-bold">
                <span className="text-white">Pield</span>
                <span className="text-neutral-400"> Privacy Firewall</span>
              </h1>
              <p className="text-sm text-neutral-500 mt-1">
                Your secrets are masked before they ever reach the LLM
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Input Section */}
        <PromptInput onSubmit={handleSubmit} loading={loading} />

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-950/30 border border-red-800/50 rounded-lg text-red-400 animate-slide-in">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                />
              </svg>
              <span>Error: {error}</span>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && <LoadingSpinner />}

        {/* Results */}
        {result && !loading && (
          <div className="mt-8 space-y-6 animate-fade-in">
            {/* Pipeline Flow */}
            <div className="bg-neutral-900/30 rounded-lg p-6 border border-neutral-800">
              <h2 className="text-lg font-semibold text-neutral-300 mb-4">
                Pipeline Flow
              </h2>
              <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
                {[
                  'User Prompt',
                  'Pield Sanitizer',
                  'Masked Prompt',
                  'LLM API',
                  'Masked Response',
                  'Restoration',
                  'Final Response',
                ].map((step, i) => (
                  <div key={i} className="flex items-center">
                    <span className="px-3 py-1 bg-neutral-800 rounded-full text-neutral-300">
                      {step}
                    </span>
                    {i < 6 && <span className="text-neutral-600 mx-2">→</span>}
                  </div>
                ))}
              </div>
            </div>

            {/* PII Status */}
            <div
              className={`p-4 rounded-lg border ${
                result.has_pii
                  ? 'bg-amber-950/30 border-amber-800/50 text-amber-400'
                  : 'bg-emerald-950/30 border-emerald-800/50 text-emerald-400'
              }`}
            >
              <span className="font-semibold">
                {result.has_pii ? 'PII Detected and Masked' : 'No PII Detected'}
              </span>
            </div>

            {/* Results Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              <ResultCard title="Original Prompt" data={result.original_prompt} type="original" />
              <ResultCard title="Masked Prompt" data={result.masked_prompt} type="masked" />
              <MetadataViewer metadata={result.metadata} />
              <ResultCard title="LLM Response (Masked)" data={result.llm_response_masked || 'No response'} type="llm" />
            </div>

            {/* Final Restored Response */}
            <ResultCard
              title="Restored Final Response"
              data={result.llm_response_restored || 'No restored response'}
              type="restored"
              fullWidth
            />
          </div>
        )}

        {/* Benchmarks */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-center mb-8">
            <span className="text-white">Benchmarks</span>
          </h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {[
              { label: 'Package Size', value: '322 KB', icon: '📦' },
              { label: 'Precision', value: '100%', icon: '🎯' },
              { label: 'F1 Score', value: '84%', icon: '📊' },
              { label: 'Latency', value: '0.77 ms', icon: '⚡' },
              { label: 'Published', value: 'PyPI', icon: '📚' },
            ].map((bench, i) => (
              <div key={i} className="bg-neutral-900 rounded-lg p-6 border border-neutral-800 card-glow text-center">
                <div className="text-3xl mb-2">{bench.icon}</div>
                <div className="text-2xl font-bold text-neutral-200">{bench.value}</div>
                <div className="text-sm text-neutral-500 mt-1">{bench.label}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-800 mt-16">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-neutral-600">
          <p>Pield Privacy Firewall — Ultra-light LLM Privacy Protection</p>
          <p className="mt-1">Built by Dipanjan Dutta using hbp100</p>
        </div>
      </footer>
    </div>
  )
}

export default App
