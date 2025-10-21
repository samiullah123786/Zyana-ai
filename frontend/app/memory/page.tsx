'use client'

import { useState } from 'react'

interface SearchResult {
  id: string
  snippet: string
  table: string
  date: string
  business: string
  score: number
}

export default function MemoryPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/memory/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 5 })
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data.results || [])
        setSummary(data.summary || '')
      }
    } catch (error) {
      console.error('Search error:', error)
      setSummary('Error performing search. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🧠 Memory Search
        </h1>
        <p className="text-gray-600">
          Search your personal memory using AI-powered semantic search
        </p>
      </header>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything... e.g., 'When did I last pay Ahmad?'"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-blue-900 mb-2">Summary</h3>
          <p className="text-blue-800">{summary}</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Search Results</h3>
          {results.map((result) => (
            <div key={result.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <p className="text-gray-900 mb-2">{result.snippet}</p>
                  <div className="flex gap-4 text-sm text-gray-500">
                    <span>📅 {result.date}</span>
                    {result.business && <span>🏢 {result.business}</span>}
                    <span>📊 {result.table}</span>
                  </div>
                </div>
                <div className="ml-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {(result.score * 100).toFixed(0)}% match
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && !results.length && !summary && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">Enter a query to search your memory</p>
          <p className="text-sm mt-2">Try: "Show me all loans" or "What were my expenses last week?"</p>
        </div>
      )}
    </div>
  )
}

