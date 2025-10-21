'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface Business {
  id: number
  name: string
  slug: string
  balance?: number
}

export default function Home() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBusinesses()
  }, [])

  const fetchBusinesses = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      // For now, hardcode sample data
      setBusinesses([
        { id: 1, name: 'Vidify', slug: 'vidify', balance: 125000 },
        { id: 2, name: 'MilkBusiness', slug: 'milk-business', balance: 85000 },
        { id: 3, name: 'Yazman Express', slug: 'yazman-express', balance: 50000 },
      ])
    } catch (error) {
      console.error('Error fetching businesses:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          👋 Welcome to Zyana
        </h1>
        <p className="text-gray-600">
          Your personal AI assistant for managing businesses, finances, and more
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {loading ? (
          <div className="col-span-3 text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading your businesses...</p>
          </div>
        ) : (
          businesses.map((business) => (
            <Link
              key={business.id}
              href={`/business/${business.slug}`}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                {business.name}
              </h2>
              <div className="text-3xl font-bold text-primary-600 mb-2">
                PKR {business.balance?.toLocaleString() || '0'}
              </div>
              <p className="text-sm text-gray-500">
                Click to view details →
              </p>
            </Link>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          href="/memory"
          className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <h3 className="text-xl font-semibold mb-2">🧠 Memory Search</h3>
          <p className="text-purple-100">
            Search through your personal memory using AI-powered semantic search
          </p>
        </Link>

        <Link
          href="/agent-console"
          className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <h3 className="text-xl font-semibold mb-2">🤖 Agent Console</h3>
          <p className="text-blue-100">
            Send commands directly to Zyana and get instant responses
          </p>
        </Link>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="bg-gray-100 hover:bg-gray-200 rounded-lg p-4 text-center transition-colors">
            <div className="text-2xl mb-2">💰</div>
            <div className="text-sm font-medium">Add Transaction</div>
          </button>
          <button className="bg-gray-100 hover:bg-gray-200 rounded-lg p-4 text-center transition-colors">
            <div className="text-2xl mb-2">📅</div>
            <div className="text-sm font-medium">Create Event</div>
          </button>
          <button className="bg-gray-100 hover:bg-gray-200 rounded-lg p-4 text-center transition-colors">
            <div className="text-2xl mb-2">🎯</div>
            <div className="text-sm font-medium">Set Goal</div>
          </button>
          <button className="bg-gray-100 hover:bg-gray-200 rounded-lg p-4 text-center transition-colors">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm font-medium">View Reports</div>
          </button>
        </div>
      </div>
    </div>
  )
}

