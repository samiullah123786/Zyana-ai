"use client"

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface SystemStats {
  total_invoices: number
  total_clients: number
  pending_notifications: number
  total_logs: number
  habit_profiles: number
  overdue_invoices: number
  overdue_amount: number
  pending_invoices: number
  pending_amount: number
  recent_activity: any[]
}

interface AgentLog {
  id: number
  agent_type: string
  action: string
  status: string
  timestamp: string
  input_data?: any
  output_data?: any
}

interface ScheduledNotification {
  id: number
  message: string
  scheduled_time: string
  status: string
  user_id: number
}

export default function AdminPage() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [logs, setLogs] = useState<AgentLog[]>([])
  const [notifications, setNotifications] = useState<ScheduledNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'notifications' | 'habits'>('overview')

  useEffect(() => {
    fetchStats()
    fetchLogs()
    fetchNotifications()
  }, [])

  const fetchStats = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/admin/stats`)
      const data = await response.json()
      setStats(data.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchLogs = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/admin/logs?limit=50`)
      const data = await response.json()
      setLogs(data.data || [])
    } catch (error) {
      console.error('Error fetching logs:', error)
    }
  }

  const fetchNotifications = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/admin/scheduled`)
      const data = await response.json()
      setNotifications(data.data || [])
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
  }

  const cancelNotification = async (notificationId: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      await fetch(`${API_URL}/notification/${notificationId}`, {
        method: 'DELETE'
      })
      fetchNotifications()
    } catch (error) {
      console.error('Error cancelling notification:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatCurrency = (amount: number) => {
    return `PKR ${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  if (loading) {
    return <div className="p-8">Loading admin dashboard...</div>
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">System overview and control panel</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium ${activeTab === 'overview' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-4 py-2 font-medium ${activeTab === 'logs' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
        >
          Activity Logs
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`px-4 py-2 font-medium ${activeTab === 'notifications' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
        >
          Scheduled Notifications
        </button>
        <button
          onClick={() => setActiveTab('habits')}
          className={`px-4 py-2 font-medium ${activeTab === 'habits' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
        >
          User Patterns
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && stats && (
        <div>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <Card className="p-6">
              <div className="text-sm text-gray-600 mb-1">Total Invoices</div>
              <div className="text-3xl font-bold">{stats.total_invoices}</div>
              <div className="text-xs text-gray-500 mt-2">
                {stats.pending_invoices} pending • {stats.overdue_invoices} overdue
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-sm text-gray-600 mb-1">Total Clients</div>
              <div className="text-3xl font-bold">{stats.total_clients}</div>
            </Card>

            <Card className="p-6">
              <div className="text-sm text-gray-600 mb-1">Pending Notifications</div>
              <div className="text-3xl font-bold">{stats.pending_notifications}</div>
            </Card>

            <Card className="p-6">
              <div className="text-sm text-gray-600 mb-1">Habit Profiles</div>
              <div className="text-3xl font-bold">{stats.habit_profiles}</div>
            </Card>
          </div>

          {/* Payment Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4">Overdue Payments</h2>
              <div className="text-3xl font-bold text-red-600 mb-2">
                {formatCurrency(stats.overdue_amount)}
              </div>
              <div className="text-sm text-gray-600">
                {stats.overdue_invoices} overdue invoices
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4">Pending Payments</h2>
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {formatCurrency(stats.pending_amount)}
              </div>
              <div className="text-sm text-gray-600">
                {stats.pending_invoices} pending invoices
              </div>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Recent Activity (Last 24 hours)</h2>
            </div>
            <div className="divide-y max-h-96 overflow-y-auto">
              {stats.recent_activity && stats.recent_activity.length > 0 ? (
                stats.recent_activity.map((log: any, index: number) => (
                  <div key={index} className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-medium">{log.agent_type}</span>
                        <span className="text-gray-600 mx-2">•</span>
                        <span className="text-gray-600">{log.action}</span>
                        <div className="text-xs text-gray-500 mt-1">
                          {formatDate(log.timestamp)}
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-gray-500">
                  No recent activity
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <Card>
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Agent Activity Logs</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{formatDate(log.timestamp)}</td>
                    <td className="px-4 py-3 text-sm font-medium">{log.agent_type}</td>
                    <td className="px-4 py-3 text-sm">{log.action}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card>
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Scheduled Notifications</h2>
          </div>
          <div className="divide-y">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No scheduled notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div key={notification.id} className="p-4 flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-medium mb-1">{notification.message}</p>
                    <p className="text-sm text-gray-600">
                      Scheduled: {formatDate(notification.scheduled_time)}
                    </p>
                    <span className={`inline-block mt-2 px-2 py-1 rounded text-xs ${
                      notification.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      notification.status === 'sent' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {notification.status}
                    </span>
                  </div>
                  {notification.status === 'pending' && (
                    <Button
                      onClick={() => cancelNotification(notification.id)}
                      size="sm"
                      variant="outline"
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Habits Tab */}
      {activeTab === 'habits' && (
        <Card>
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">User Patterns & Habits</h2>
          </div>
          <div className="p-8 text-center text-gray-500">
            <p>Work pattern analysis and habit profiles</p>
            <p className="text-sm mt-2">Patterns are learned from user activity over time</p>
          </div>
        </Card>
      )}
    </div>
  )
}

