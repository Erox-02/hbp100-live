import { useState } from 'react'

function PromptInput({ onSubmit, loading }) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (prompt.trim() && !loading) {
      onSubmit(prompt)
    }
  }

  const examplePrompts = [
    "I was born on 23rd March 1995.",
    "Convert 15 June 2024 to hijri calander calendar",
    "My email is john@gamil.com , how to access my spam in gmail??",
  ]

  return (
    <div className="bg-gray-950 rounded-lg p-6 border border-gray-800 card-glow">
      <form onSubmit={handleSubmit}>
        <label className="block text-lg font-semibold text-gray-300 mb-3">
          Enter Your Prompt
        </label>
        
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type a prompt containing sensitive information or ask about zodiac..."
          className="w-full h-32 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500 transition-colors resize-none"
          disabled={loading}
        />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mt-4 gap-3 sm:gap-0">
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setPrompt(example)}
                className="px-3 py-1 text-xs bg-gray-800 border border-gray-700 rounded-lg text-gray-400 hover:border-gray-500 hover:text-gray-200 transition-colors"
                disabled={loading}
              >
                Example {i + 1}
              </button>
            ))}
          </div>
          
          <button
            type="submit"
            disabled={!prompt.trim() || loading}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span>Sanitize & Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}

export default PromptInput
