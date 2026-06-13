import { useState, useEffect } from 'react'
import PromptInput from './components/PromptInput'
import ResultCard from './components/ResultCard'
import MetadataViewer from './components/MetadataViewer'
import LoadingSpinner from './components/LoadingSpinner'

const API_URL = import.meta.env.DEV
  ? 'http://localhost:8000/'
  : 'https://hbp100-live-api.vercel.app/'

function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [useRealLLM, setUseRealLLM] = useState(true)
  const [usePrivacy, setUsePrivacy] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}warmup`).catch(() => {})
  }, [])

  useEffect(() => {
    if (result && !loading) {
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      }, 100)
    }
  }, [result, loading])

  const handleWarmup = () => {
    fetch(`${API_URL}warmup`).catch(() => {})
  }

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
        body: JSON.stringify({ 
          prompt, 
          use_real_llm: useRealLLM,
          use_privacy: usePrivacy 
        }),
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
      <header className="border-b border-gray-800 bg-gray-950/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 sm:space-x-4">
              <div className="w-8 h-8 sm:w-12 sm:h-12 bg-gray-800 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 sm:w-8 sm:h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl sm:text-3xl font-bold">
                  <span className="text-white">HBP100</span>
                  <span className="text-gray-500">: Privacy Firewall</span>
                </h1>
                <p className="text-xs sm:text-sm text-gray-500 mt-0.5 sm:mt-1">
                  Your secrets are masked before they ever reach the LLM
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setUsePrivacy(!usePrivacy)}
                className={`px-3 py-1.5 text-xs sm:text-sm rounded-lg transition-all duration-200 font-medium ${
                  usePrivacy 
                    ? 'bg-emerald-600/20 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-600/30' 
                    : 'bg-gray-800 border border-gray-700 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {usePrivacy ? 'Privacy ON' : 'Privacy OFF'}
              </button>
              <button
                onClick={() => setUseRealLLM(!useRealLLM)}
                className={`px-3 py-1.5 text-xs sm:text-sm rounded-lg transition-all duration-200 font-medium ${
                  useRealLLM 
                    ? 'bg-yellow-600/20 border border-yellow-500/50 text-yellow-400 hover:bg-yellow-600/30' 
                    : 'bg-gray-800 border border-gray-700 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {useRealLLM ? 'BETA: Real LLM' : 'Mock Mode'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <PromptInput 
          onSubmit={handleSubmit} 
          loading={loading} 
          onWarmup={handleWarmup}
        />

        <div className="mt-4 space-y-2">
          <div className={`p-2 rounded-lg text-center border ${
            usePrivacy 
              ? 'bg-emerald-600/10 border-emerald-500/30' 
              : 'bg-red-950/30 border-red-800/50'
          }`}>
            <p className="text-xs">
              {usePrivacy 
                ? 'PRIVACY MODE: Your data is masked before reaching the LLM' 
                : 'RAW MODE: Your data is sent directly to the LLM (no privacy protection)'}
            </p>
          </div>
          <div className="p-2 bg-yellow-600/10 border border-yellow-500/30 rounded-lg text-center">
            <p className="text-xs text-yellow-400">
              {useRealLLM 
                ? '⚠️ BETA MODE: Using real Groq LLM. Responses may vary.'
                : '✓ MOCK MODE: Using simulated responses.'}
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-red-950/30 border border-red-800/50 rounded-lg text-red-400 animate-slide-in">
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" clipRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" />
              </svg>
              <span className="text-sm sm:text-base">Error: {error}</span>
            </div>
          </div>
        )}

        {loading && <LoadingSpinner />}

        {/* Added id="results" to the results container */}
        {result && !loading && (
          <div id="results" className="mt-6 sm:mt-8 space-y-4 sm:space-y-6 animate-fade-in">
            <div className="bg-gray-950/50 rounded-lg p-4 sm:p-6 border border-gray-800">
              <h2 className="text-base sm:text-lg font-semibold text-gray-300 mb-3 sm:mb-4">
                Pipeline Flow
              </h2>
              <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-xs sm:text-sm">
                {[
                  'User Prompt',
                  usePrivacy ? 'Pield Sanitizer (ON)' : 'Pield Sanitizer (OFF)',
                  usePrivacy ? 'Masked Prompt' : 'Raw Prompt',
                  useRealLLM ? 'Groq LLM (BETA)' : 'Mock LLM',
                  'Response',
                  usePrivacy ? 'Restoration' : 'No Restoration',
                  'Final Response',
                ].map((step, i) => (
                  <div key={i} className="flex items-center">
                    <span className={`px-2 sm:px-3 py-1 rounded-full text-gray-300 ${
                      step === 'Groq LLM (BETA)' ? 'bg-yellow-600/20 border border-yellow-500/50' : 
                      step === 'Pield Sanitizer (ON)' ? 'bg-emerald-600/20 border border-emerald-500/50' :
                      'bg-gray-800'
                    }`}>
                      {step}
                    </span>
                    {i < 6 && <span className="text-gray-600 mx-1 sm:mx-2">→</span>}
                  </div>
                ))}
              </div>
            </div>

            {usePrivacy && result.has_pii && (
              <div className="p-4 rounded-lg border bg-emerald-950/30 border-emerald-800/50 text-emerald-400">
                <span className="font-semibold">PII Detected and Masked</span>
              </div>
            )}

            {usePrivacy && !result.has_pii && (
              <div className="p-4 rounded-lg border bg-gray-800/30 border-gray-700 text-gray-400">
                <span className="font-semibold">✓ No PII Detected</span>
              </div>
            )}

            {!usePrivacy && (
              <div className="p-4 rounded-lg border bg-red-950/30 border-red-800/50 text-red-400">
                <span className="font-semibold">⚠️ PRIVACY OFF: Your data is sent directly to the LLM</span>
              </div>
            )}

            <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2">
              <ResultCard title="Original Prompt" data={result.original_prompt} type="original" />
              {usePrivacy && (
                <ResultCard title="Masked Prompt" data={result.masked_prompt} type="masked" />
              )}
              {usePrivacy && (
                <MetadataViewer metadata={result.metadata} />
              )}
              <ResultCard 
                title={useRealLLM ? "LLM Response [BETA]" : "LLM Response (Mock)"} 
                data={result.llm_response_masked || 'No response'} 
                type="llm" 
              />
            </div>

            {usePrivacy && (
              <ResultCard
                title="Restored Final Response"
                data={result.llm_response_restored || 'No restored response'}
                type="restored"
                fullWidth
              />
            )}

            {!usePrivacy && (
              <ResultCard
                title="Final Response (Raw)"
                data={result.llm_response_masked || 'No response'}
                type="original"
                fullWidth
              />
            )}
          </div>
        )}

        <div className="mt-12 sm:mt-16">
          <h2 className="text-xl sm:text-2xl font-bold text-center mb-6 sm:mb-8 text-white">
            Benchmarks
          </h2>
          <div className="grid gap-3 sm:gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
            {[
              { label: 'Package Size', value: '322 KB', icon: '📦' },
              { label: 'Precision', value: '100%', icon: '🎯' },
              { label: 'F1 Score', value: '84%', icon: '📊' },
              { label: 'Latency', value: '0.77 ms', icon: '⚡' },
              { label: 'Published', value: 'PyPI', icon: '📚' },
            ].map((bench, i) => (
              <div key={i} className="bg-gray-950 rounded-lg p-3 sm:p-6 border border-gray-800 card-glow text-center">
                <div className="text-2xl sm:text-3xl mb-1 sm:mb-2">{bench.icon}</div>
                <div className="text-base sm:text-2xl font-bold text-gray-200">{bench.value}</div>
                <div className="text-xs sm:text-sm text-gray-500 mt-0.5 sm:mt-1">{bench.label}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 mt-12 sm:mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 text-center text-xs sm:text-sm text-gray-600">
          <p>Hbp100 Privacy Firewall — Ultra-light LLM Privacy Protection</p>
          <p className="mt-1">Built by Erox-02 using hbp100</p>
        </div>
      </footer>
    </div>
  )
}

export default App
