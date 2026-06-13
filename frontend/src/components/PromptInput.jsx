import { useState, useRef } from 'react'

function PromptInput({ onSubmit, loading, onWarmup }) {
const [prompt, setPrompt] = useState('')
const warmedUpRef = useRef(false)

const triggerWarmup = () => {
if (warmedUpRef.current) return

warmedUpRef.current = true
onWarmup()

}

const handleSubmit = (e) => {
e.preventDefault()

if (prompt.trim() && !loading) {
  onSubmit(prompt)
}

}

const examples = [
"My birthday is 14th August 2009. What's my zodiac sign?",
"I was born on 23 March 1995. Tell me my horoscope.",
"Convert 15 June 2024 to Hijri calendar",
"My email is john@gmail.com and SSN is 123-45-6789"
]

const copyToClipboard = (text) => {
navigator.clipboard.writeText(text)
triggerWarmup()
}

return (
<div className="bg-gray-950 rounded-lg p-6 border border-gray-800 card-glow">
<label className="block text-lg font-semibold text-gray-300 mb-3">
Enter Your Prompt
</label>

  <form onSubmit={handleSubmit}>
    <textarea
      value={prompt}
      onChange={(e) => setPrompt(e.target.value)}
      onFocus={triggerWarmup}
      onPaste={triggerWarmup}
      placeholder="Click here and start typing..."
      className="w-full h-32 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500 transition-colors resize-none"
      disabled={loading}
    />

    <div className="mt-4 p-3 bg-gray-900/50 rounded-lg border border-gray-800">
      <p className="text-xs text-gray-500 mb-2">
        Try typing or copy-paste:
      </p>

      {examples.map((example, idx) => (
        <div
          key={idx}
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2 last:mb-0"
        >
          <code className="text-xs text-gray-400 break-words">
            {example}
          </code>

          <button
            type="button"
            onClick={() => copyToClipboard(example)}
            className="self-start sm:self-auto text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-md transition-all"
          >
            Copy
          </button>
        </div>
      ))}
    </div>

    <div className="flex justify-end mt-4">
      <button
        type="submit"
        disabled={!prompt.trim() || loading}
        className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center space-x-2"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>

        <span>Sanitize & Send</span>
      </button>
    </div>
  </form>
</div>

)
}

export default PromptInput
