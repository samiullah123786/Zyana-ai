'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  Calendar,
  Users,
  FileText,
  Plus,
  Filter,
  Download
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatCard } from '@/components/ui/stat-card'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'
import { api } from '@/lib/api'

interface Transaction {
  id: string | number
  type: 'income' | 'expense' | 'loan'
  description: string
  amount: number
  date: string
  category: string
}

interface BusinessData {
  id: number
  name: string
  slug: string
  balance: number
  revenue: number
  expenses: number
  profit: number
  revenueChange: number
  transactions: Transaction[]
}

interface ChartData {
  month?: string
  revenue?: number
  expenses?: number
  name?: string
  value?: number
  color?: string
}

export default function BusinessDetailPage() {
  const params = useParams()
  const slug = params?.slug as string
  const [business, setBusiness] = useState<BusinessData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month')
  const [revenueData, setRevenueData] = useState<ChartData[]>([])
  const [categoryData, setCategoryData] = useState<ChartData[]>([])

  useEffect(() => {
    fetchBusinessData()
  }, [slug])

  const fetchBusinessData = async () => {
    try {
      // Get business by slug
      const businessRes = await api.getBusinessBySlug(slug)
      
      if (!businessRes) {
        setBusiness(null)
        setLoading(false)
        return
      }

      // Fetch business summary and analytics
      const [summary, transactions, monthlyTrend, categories] = await Promise.all([
        api.getBusinessSummary(businessRes.id).catch(() => ({ total_income: 0, total_expenses: 0, balance: 0 })),
        api.getTransactions(businessRes.id).catch(() => []),
        api.getMonthlyTrend(businessRes.id, 6).catch(() => []),
        api.getCategoryBreakdown(businessRes.id, 'income').catch(() => [])
      ])

      // Calculate profit
      const profit = (summary.total_income || 0) - (summary.total_expenses || 0)

      setBusiness({
        id: businessRes.id,
        name: businessRes.name,
        slug: businessRes.slug,
        balance: summary.balance || 0,
        revenue: summary.total_income || 0,
        expenses: summary.total_expenses || 0,
        profit: profit,
        revenueChange: 0, // Can be calculated from historical data
        transactions: transactions.slice(0, 10).map((t: any) => ({
          id: t.id,
          type: t.type,
          description: t.description || `${t.type} transaction`,
          amount: t.amount,
          date: t.date,
          category: t.category || 'Other'
        }))
      })

      // Set chart data
      if (monthlyTrend && monthlyTrend.length > 0) {
        setRevenueData(monthlyTrend)
      }

      if (categories && categories.length > 0) {
        setCategoryData(categories)
      }

      console.log('✅ Loaded business data:', businessRes.name)
    } catch (error) {
      console.error('Error fetching business data:', error)
      setBusiness(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading business data...</p>
        </div>
      </div>
    )
  }

  if (!business) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-2xl text-gray-600 mb-4">Business not found</p>
          <Link href="/">
            <Button>Back to Dashboard</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="w-5 h-5" />
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{business.name}</h1>
                <p className="text-gray-600">Business Overview & Analytics</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add Transaction
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Current Balance"
            value={formatCurrency(business.balance)}
            change={business.revenueChange}
            icon={DollarSign}
            gradient="bg-gradient-to-br from-blue-500 to-blue-600"
          />
          <StatCard
            title="Total Revenue"
            value={formatCurrency(business.revenue)}
            change={business.revenueChange}
            icon={TrendingUp}
            gradient="bg-gradient-to-br from-green-500 to-green-600"
          />
          <StatCard
            title="Total Expenses"
            value={formatCurrency(business.expenses)}
            change={-3.2}
            icon={TrendingDown}
            gradient="bg-gradient-to-br from-orange-500 to-orange-600"
          />
          <StatCard
            title="Net Profit"
            value={formatCurrency(business.profit)}
            change={22.5}
            icon={DollarSign}
            gradient="bg-gradient-to-br from-purple-500 to-purple-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Revenue vs Expenses Chart */}
          <div className="animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle>Revenue vs Expenses</CardTitle>
              </CardHeader>
              <CardContent>
                {revenueData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={revenueData}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                        </linearGradient>
                        <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
                      <YAxis stroke="#9ca3af" fontSize={12} />
                      <Tooltip
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                        formatter={(value: number) => formatCurrency(value)}
                      />
                      <Legend />
                      <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} fill="url(#colorRevenue)" />
                      <Area type="monotone" dataKey="expenses" stroke="#f59e0b" strokeWidth={2} fill="url(#colorExpense)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p>No revenue data available</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Category Distribution */}
          <div className="animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle>Income by Category</CardTitle>
              </CardHeader>
              <CardContent>
                {categoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                        label={(entry) => {
                          const total = categoryData.reduce((sum, item) => sum + (item.value || 0), 0)
                          return `${entry.name} (${((entry.value / total) * 100).toFixed(0)}%)`
                        }}
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p>No category data available</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="animate-fade-in">
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              {business.transactions.length > 0 ? (
                <div className="space-y-4">
                  {business.transactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        transaction.type === 'income' 
                          ? 'bg-green-100 text-green-600' 
                          : transaction.type === 'expense'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-blue-100 text-blue-600'
                      }`}>
                        {transaction.type === 'income' ? (
                          <TrendingUp className="w-6 h-6" />
                        ) : transaction.type === 'expense' ? (
                          <TrendingDown className="w-6 h-6" />
                        ) : (
                          <Users className="w-6 h-6" />
                        )}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{transaction.description}</p>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <span>{formatDate(transaction.date)}</span>
                          <span>•</span>
                          <Badge variant="outline">{transaction.category}</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${
                        transaction.type === 'income' 
                          ? 'text-green-600' 
                          : transaction.type === 'expense'
                          ? 'text-red-600'
                          : 'text-blue-600'
                      }`}>
                        {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </p>
                    </div>
                  </div>
                  ))}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No transactions yet</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
