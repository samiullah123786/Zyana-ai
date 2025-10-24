'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  DollarSign,
  TrendingUp,
  Building2,
  Activity,
  Plus,
  Calendar,
  Target,
  FileText,
  Sparkles,
  ArrowUpRight,
  Clock
} from 'lucide-react'
import { StatCard } from '@/components/ui/stat-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface Business {
  id: number
  name: string
  slug: string
  balance?: number
  revenue?: number
  expenses?: number
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
      
      // Try to fetch real data from backend
      try {
        const response = await fetch(`${apiUrl}/profile/businesses`)
        if (response.ok) {
          const data = await response.json()
          setBusinesses(data.businesses || [])
          setLoading(false)
          return
        }
      } catch (apiError) {
        console.log('Backend not available, using demo data:', apiError)
      }
      
      // Fallback to demo data if backend is not available
      setBusinesses([
        { id: 1, name: 'Vidify', slug: 'vidify', balance: 125000, revenue: 180000, expenses: 55000 },
        { id: 2, name: 'MilkBusiness', slug: 'milk-business', balance: 85000, revenue: 120000, expenses: 35000 },
        { id: 3, name: 'Yazman Express', slug: 'yazman-express', balance: 50000, revenue: 75000, expenses: 25000 },
      ])
    } catch (error) {
      console.error('Error fetching businesses:', error)
    } finally {
      setLoading(false)
    }
  }

  // Sample chart data
  const revenueData = [
    { month: 'Jan', value: 45000 },
    { month: 'Feb', value: 52000 },
    { month: 'Mar', value: 48000 },
    { month: 'Apr', value: 61000 },
    { month: 'May', value: 55000 },
    { month: 'Jun', value: 67000 },
  ]

  const businessData = [
    { name: 'Vidify', value: 125000 },
    { name: 'Milk', value: 85000 },
    { name: 'Yazman', value: 50000 },
  ]

  const recentActivities = [
    { id: 1, type: 'transaction', message: 'Received payment from client', amount: '+PKR 25,000', time: '2 hours ago', color: 'text-green-600' },
    { id: 2, type: 'expense', message: 'Office supplies purchased', amount: '-PKR 3,500', time: '4 hours ago', color: 'text-red-600' },
    { id: 3, type: 'event', message: 'Meeting with investor scheduled', amount: '', time: '1 day ago', color: 'text-blue-600' },
    { id: 4, type: 'goal', message: 'Monthly revenue target achieved', amount: '', time: '2 days ago', color: 'text-purple-600' },
  ]

  const totalBalance = businesses.reduce((sum, b) => sum + (b.balance || 0), 0)
  const totalRevenue = businesses.reduce((sum, b) => sum + (b.revenue || 0), 0)
  const totalExpenses = businesses.reduce((sum, b) => sum + (b.expenses || 0), 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      {/* Hero Section with Animated Background */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white z-0">
        <div className="absolute inset-0 bg-grid-white/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 animate-slide-up z-0">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="w-6 h-6" />
            <span className="text-sm font-semibold uppercase tracking-wide">AI-Powered Dashboard</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Welcome back! 👋
          </h1>
          <p className="text-xl text-white/90 max-w-2xl">
            Here's what's happening with your businesses today
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 -mt-16">
          <StatCard
            title="Total Balance"
            value={formatCurrency(totalBalance)}
            change={12.5}
            icon={DollarSign}
            gradient="bg-gradient-to-br from-blue-500 to-blue-600"
            delay={0}
          />
          <StatCard
            title="Total Revenue"
            value={formatCurrency(totalRevenue)}
            change={18.2}
            icon={TrendingUp}
            gradient="bg-gradient-to-br from-green-500 to-green-600"
            delay={0.1}
          />
          <StatCard
            title="Total Expenses"
            value={formatCurrency(totalExpenses)}
            change={-5.4}
            icon={Activity}
            gradient="bg-gradient-to-br from-orange-500 to-orange-600"
            delay={0.2}
          />
          <StatCard
            title="Active Businesses"
            value={businesses.length}
            icon={Building2}
            gradient="bg-gradient-to-br from-purple-500 to-purple-600"
            delay={0.3}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Revenue Chart */}
          <div className="animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Revenue Trend</span>
                  <Badge variant="success">+15.3%</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={revenueData}>
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
                    <YAxis stroke="#9ca3af" fontSize={12} />
                    <Tooltip
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorRevenue)" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Business Comparison */}
          <div className="animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle>Business Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={businessData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                    <YAxis stroke="#9ca3af" fontSize={12} />
                    <Tooltip
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Bar dataKey="value" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Businesses List */}
          <div className="lg:col-span-2 animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle>Your Businesses</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading your businesses...</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {businesses.map((business, index) => (
                      <div key={business.id} className="animate-fade-in">
                        <Link href={`/business/${business.slug}`}>
                          <div className="group p-4 rounded-xl border border-gray-200 hover:border-blue-300 bg-white hover:bg-blue-50/50 transition-all duration-200 hover:shadow-md">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl">
                                  {business.name[0]}
                                </div>
                                <div>
                                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                                    {business.name}
                                  </h3>
                                  <p className="text-sm text-gray-500">
                                    Balance: {formatCurrency(business.balance || 0)}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="flex items-center space-x-2 text-sm text-green-600 font-medium mb-1">
                                  <TrendingUp className="w-4 h-4" />
                                  <span>{formatCurrency(business.revenue || 0)}</span>
                                </div>
                                <Button size="sm" variant="ghost" className="group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                  View Details
                                  <ArrowUpRight className="w-4 h-4 ml-1" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <div className="animate-fade-in">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivities.map((activity, index) => (
                    <div
                      key={activity.id}
                      className="border-l-2 border-gray-200 pl-4 pb-4 last:pb-0 animate-fade-in"
                    >
                      <p className="text-sm text-gray-900 mb-1">{activity.message}</p>
                      {activity.amount && (
                        <p className={`text-sm font-semibold ${activity.color} mb-1`}>
                          {activity.amount}
                        </p>
                      )}
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="animate-fade-in">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/transactions/new">
                  <Button variant="outline" className="w-full h-24 flex-col space-y-2 hover:scale-105 transition-transform">
                    <Plus className="w-6 h-6 text-blue-600" />
                    <span className="text-sm font-medium">Add Transaction</span>
                  </Button>
                </Link>
                <Link href="/calendar">
                  <Button variant="outline" className="w-full h-24 flex-col space-y-2 hover:scale-105 transition-transform">
                    <Calendar className="w-6 h-6 text-green-600" />
                    <span className="text-sm font-medium">Create Event</span>
                  </Button>
                </Link>
                <Link href="/goals">
                  <Button variant="outline" className="w-full h-24 flex-col space-y-2 hover:scale-105 transition-transform">
                    <Target className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium">Set Goal</span>
                  </Button>
                </Link>
                <Link href="/reports">
                  <Button variant="outline" className="w-full h-24 flex-col space-y-2 hover:scale-105 transition-transform">
                    <FileText className="w-6 h-6 text-orange-600" />
                    <span className="text-sm font-medium">View Reports</span>
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8 animate-fade-in">
          <Link href="/memory">
            <Card className="h-full bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer">
              <CardContent className="p-8">
                <div className="flex items-start justify-between mb-4">
                  <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <Badge variant="outline" className="text-white border-white/50">AI Powered</Badge>
                </div>
                <h3 className="text-2xl font-bold mb-2">🧠 Memory Search</h3>
                <p className="text-purple-100">
                  Search through your personal memory using AI-powered semantic search. Find anything instantly!
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/agent-console">
            <Card className="h-full bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer">
              <CardContent className="p-8">
                <div className="flex items-start justify-between mb-4">
                  <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
                    <Activity className="w-8 h-8" />
                  </div>
                  <Badge variant="outline" className="text-white border-white/50">Live</Badge>
                </div>
                <h3 className="text-2xl font-bold mb-2">🤖 Agent Console</h3>
                <p className="text-blue-100">
                  Send commands directly to Zyana AI and get instant intelligent responses.
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  )
}

