'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

interface Transaction {
  id: number
  type: string
  amount: number
  currency: string
  category: string
  person: string | null
  date: string
  description: string | null
}

export default function BusinessPage() {
  const params = useParams()
  const slug = params.slug as string
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState({
    income: 0,
    expenses: 0,
    balance: 0
  })

  useEffect(() => {
    fetchTransactions()
  }, [slug])

  const fetchTransactions = async () => {
    try {
      // For now, use sample data
      const sampleData = [
        {
          id: 1,
          type: 'income',
          amount: 50000,
          currency: 'PKR',
          category: 'sales',
          person: null,
          date: '2025-10-20',
          description: 'Client payment for video project'
        },
        {
          id: 2,
          type: 'expense',
          amount: 15000,
          currency: 'PKR',
          category: 'software',
          person: null,
          date: '2025-10-18',
          description: 'Adobe subscription'
        },
        {
          id: 3,
          type: 'expense',
          amount: 10000,
          currency: 'PKR',
          category: 'loan',
          person: 'Ahmad',
          date: '2025-10-15',
          description: 'Loan to Ahmad'
        }
      ]
      
      setTransactions(sampleData)
      
      const income = sampleData
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0)
      const expenses = sampleData
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0)
      
      setSummary({
        income,
        expenses,
        balance: income - expenses
      })
    } catch (error) {
      console.error('Error fetching transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const businessName = slug.split('-').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/" className="text-primary-600 hover:text-primary-700">
          ← Back to Dashboard
        </Link>
      </div>

      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          {businessName}
        </h1>
        <p className="text-gray-600">Business financial overview</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-green-800 mb-2">Total Income</h3>
          <p className="text-3xl font-bold text-green-600">
            PKR {summary.income.toLocaleString()}
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-red-800 mb-2">Total Expenses</h3>
          <p className="text-3xl font-bold text-red-600">
            PKR {summary.expenses.toLocaleString()}
          </p>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Balance</h3>
          <p className="text-3xl font-bold text-blue-600">
            PKR {summary.balance.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Recent Transactions</h2>
        </div>
        
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Person</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(transaction.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        transaction.type === 'income' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {transaction.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.person || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {transaction.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span className={transaction.type === 'income' ? 'text-green-600' : 'text-red-600'}>
                        {transaction.type === 'income' ? '+' : '-'}
                        {transaction.currency} {transaction.amount.toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

