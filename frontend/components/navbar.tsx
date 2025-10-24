'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Bell, Search, Menu, X, Bot, Settings, LogOut, User } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { getInitials } from '@/lib/utils'

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  const notifications = [
    { id: 1, message: 'New transaction added to Vidify', time: '2m ago', unread: true },
    { id: 2, message: 'Calendar event tomorrow at 10 AM', time: '1h ago', unread: true },
    { id: 3, message: 'Monthly report ready', time: '3h ago', unread: false },
  ]

  const unreadCount = notifications.filter(n => n.unread).length

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-2 rounded-lg group-hover:scale-110 transition-transform duration-200">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Zyana
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Search Button */}
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
            >
              <Search className="w-5 h-5 text-gray-600" />
            </button>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-semibold">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Notifications Dropdown */}
              <AnimatePresence>
                {notificationsOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden"
                  >
                    <div className="p-4 border-b border-gray-200">
                      <h3 className="font-semibold text-gray-900">Notifications</h3>
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={`p-4 hover:bg-gray-50 transition-colors border-b border-gray-100 ${
                            notification.unread ? 'bg-blue-50/50' : ''
                          }`}
                        >
                          <p className="text-sm text-gray-900">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                        </div>
                      ))}
                    </div>
                    <div className="p-3 border-t border-gray-200">
                      <button className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium">
                        View all notifications
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* User Avatar */}
            <div className="flex items-center space-x-3 pl-3 border-l border-gray-300">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white font-semibold">
                {getInitials('Zyana User')}
              </div>
              <div className="text-sm">
                <p className="font-medium text-gray-900">Zyana User</p>
                <p className="text-xs text-gray-500">Admin</p>
              </div>
            </div>

            {/* Settings */}
            <Link href="/settings">
              <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6 text-gray-900" />
            ) : (
              <Menu className="w-6 h-6 text-gray-900" />
            )}
          </button>
        </div>
      </div>

      {/* Search Bar (Expandable) */}
      <AnimatePresence>
        {searchOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 overflow-hidden"
          >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search businesses, transactions, memories..."
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden border-t border-gray-200 bg-white"
          >
            <div className="px-4 py-4 space-y-3">
              <Link href="/" className="block px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                Dashboard
              </Link>
              <Link href="/memory" className="block px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                Memory Search
              </Link>
              <Link href="/agent-console" className="block px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                Agent Console
              </Link>
              <Link href="/settings" className="block px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                Settings
              </Link>
              <button className="w-full text-left px-4 py-2 rounded-lg hover:bg-red-50 text-red-600 transition-colors">
                <LogOut className="w-4 h-4 inline mr-2" />
                Logout
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

