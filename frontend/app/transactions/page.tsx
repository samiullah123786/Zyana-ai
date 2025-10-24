'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Filter,
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  User,
  Building2,
  Save,
  X
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency } from '@/lib/utils'

interface Transaction {
  id: number
  business_id: number
  type: 'income' | 'expense' | 'transfer'
  amount: number
  currency: string
  category?: string
  person?: string
  date: string
  description?: string
  businesses?: { name: string }
}

interface Business {
  id: number
  name: string
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [filterType, setFilterType] = useState<string>('all')
  const [filterBusiness, setFilterBusiness] = useState<number | null>(null)

  useEffect(() => {
    fetchData()
  }, [filterType, filterBusiness])

  const fetchData = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // Fetch businesses
      const businessesRes = await fetch(`${apiUrl}/finance/businesses`)
      if (businessesRes.ok) {
        const businessesData = await businessesRes.json()
        setBusinesses(businessesData || [])
      }

      // Fetch transactions
      let url = `${apiUrl}/finance/transactions?limit=100`
      if (filterType !== 'all') {
        url += `&type=${filterType}`
      }
      if (filterBusiness) {
        url += `&business_id=${filterBusiness}`
      }

      const transactionsRes = await fetch(url)
      if (transactionsRes.ok) {
        const transactionsData = await transactionsRes.json()
        setTransactions(transactionsData || [])
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)

  const totalExpenses = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
              <p className="text-gray-600 mt-2">Manage all your income and expenses</p>
            </div>
            <Button 
              onClick={() => setShowAddModal(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Transaction
            </Button>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Income</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {formatCurrency(totalIncome)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Expenses</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">
                      {formatCurrency(totalExpenses)}
                    </p>
                  </div>
                  <div className="p-3 bg-red-100 rounded-lg">
                    <TrendingDown className="w-6 h-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Net Flow</p>
                    <p className={`text-2xl font-bold mt-1 ${totalIncome - totalExpenses >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                      {formatCurrency(totalIncome - totalExpenses)}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Type
                  </label>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Types</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                    <option value="transfer">Transfer</option>
                  </select>
                </div>

                <div className="flex-1 min-w-[200px]">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business
                  </label>
                  <select
                    value={filterBusiness || ''}
                    onChange={(e) => setFilterBusiness(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Businesses</option>
                    {businesses.map((business) => (
                      <option key={business.id} value={business.id}>
                        {business.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-end">
                  <Button variant="outline">
                    <Filter className="w-4 h-4 mr-2" />
                    More Filters
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Transactions List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading transactions...</p>
          </div>
        ) : transactions.length === 0 ? (
          <Card>
            <CardContent className="text-center py-16">
              <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Transactions Yet</h3>
              <p className="text-gray-600 mb-6">Start by adding your first transaction</p>
              <Button onClick={() => setShowAddModal(true)} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Add Transaction
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions ({transactions.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {transactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-4 flex-1">
                      <div className={`p-3 rounded-lg ${
                        transaction.type === 'income' ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {transaction.type === 'income' ? (
                          <TrendingUp className={`w-5 h-5 ${
                            transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                          }`} />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-600" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="font-medium text-gray-900">
                            {transaction.category || 'Uncategorized'}
                          </p>
                          <Badge variant="outline">{transaction.type}</Badge>
                        </div>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          {transaction.businesses && (
                            <span className="flex items-center">
                              <Building2 className="w-3 h-3 mr-1" />
                              {transaction.businesses.name}
                            </span>
                          )}
                          {transaction.person && (
                            <span className="flex items-center">
                              <User className="w-3 h-3 mr-1" />
                              {transaction.person}
                            </span>
                          )}
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(transaction.date).toLocaleDateString()}
                          </span>
                        </div>
                        {transaction.description && (
                          <p className="text-sm text-gray-500 mt-1">{transaction.description}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className={`text-lg font-semibold ${
                          transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.type === 'income' ? '+' : '-'}
                          {formatCurrency(transaction.amount)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Add Transaction Modal */}
      {showAddModal && (
        <TransactionModal
          businesses={businesses}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            fetchData()
            setShowAddModal(false)
          }}
        />
      )}
    </div>
  )
}

function TransactionModal({ 
  businesses,
  onClose, 
  onSuccess 
}: { 
  businesses: Business[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    business_id: businesses[0]?.id || 0,
    type: 'expense' as 'income' | 'expense' | 'transfer',
    amount: '',
    currency: 'PKR',
    category: '',
    person: '',
    date: new Date().toISOString().split('T')[0],
    description: ''
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('API URL:', apiUrl)
      console.log('Transaction data:', formData)
      
      const response = await fetch(`${apiUrl}/finance/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      console.log('Response status:', response.status)
      const responseData = await response.json()
      console.log('Response data:', responseData)
      
      if (response.ok) {
        alert('✅ Transaction added successfully!')
        onSuccess()
      } else {
        alert(`❌ Failed to add transaction: ${responseData.detail || JSON.stringify(responseData)}`)
      }
    } catch (error) {
      console.error('Error adding transaction:', error)
      alert(`❌ Error adding transaction: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-[120] flex items-center justify-center p-4 animate-fade-in">
      <Card className="w-full max-w-md animate-slide-up max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Add Transaction</CardTitle>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business *
              </label>
              <select
                required
                value={formData.business_id}
                onChange={(e) => setFormData({ ...formData, business_id: Number(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {businesses.map((business) => (
                  <option key={business.id} value={business.id}>
                    {business.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type *
              </label>
              <select
                required
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="income">Income</option>
                <option value="expense">Expense</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount * (PKR)
              </label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Sales, Rent, Salary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Person
              </label>
              <input
                type="text"
                value={formData.person}
                onChange={(e) => setFormData({ ...formData, person: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Ahmad, Client Name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date *
              </label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Optional notes..."
              />
            </div>

            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Add Transaction
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

