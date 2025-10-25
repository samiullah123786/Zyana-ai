'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Agent {
  name: string
  icon: string
  description: string
  status: 'active' | 'idle' | 'offline'
  capabilities: string[]
  route: string
  color: string
  stats?: {
    label: string
    value: string
  }[]
}

const agents: Agent[] = [
  {
    name: 'Calendar Agent',
    icon: '📅',
    description: 'Schedule meetings, events, and reminders with Google Calendar integration',
    status: 'active',
    capabilities: [
      'Natural language scheduling',
      'Google Calendar sync',
      'Multi-turn clarification',
      'Timezone-aware parsing',
      'Conflict detection'
    ],
    route: '/calendar',
    color: 'from-blue-500 to-cyan-500',
    stats: [
      { label: 'Events Today', value: '3' },
      { label: 'This Week', value: '12' }
    ]
  },
  {
    name: 'Finance Agent',
    icon: '💰',
    description: 'Track expenses, income, invoices, and generate financial reports',
    status: 'active',
    capabilities: [
      'Expense & income tracking',
      'Invoice management',
      'Loan tracking',
      'Monthly reports',
      'Multi-business support'
    ],
    route: '/transactions',
    color: 'from-green-500 to-emerald-500',
    stats: [
      { label: 'This Month', value: 'PKR 45K' },
      { label: 'Pending', value: '3' }
    ]
  },
  {
    name: 'Voice Agent',
    icon: '🎙️',
    description: 'Process voice messages with Groq Whisper AI transcription',
    status: 'active',
    capabilities: [
      'Voice transcription',
      'Multi-language support',
      'Fast processing (<2s)',
      'High accuracy',
      'Background processing'
    ],
    route: '/agent-console',
    color: 'from-purple-500 to-pink-500',
    stats: [
      { label: 'Processed', value: '127' },
      { label: 'Accuracy', value: '98%' }
    ]
  },
  {
    name: 'Invoice Agent',
    icon: '📊',
    description: 'Generate invoices and send payment reminders',
    status: 'active',
    capabilities: [
      'Invoice generation',
      'Payment tracking',
      'Overdue reminders',
      'Monthly reports',
      'Client management'
    ],
    route: '/invoices',
    color: 'from-orange-500 to-red-500',
    stats: [
      { label: 'Pending', value: '5' },
      { label: 'Paid', value: 'PKR 125K' }
    ]
  },
  {
    name: 'Client Agent',
    icon: '👥',
    description: 'Manage client relationships and project assignments',
    status: 'active',
    capabilities: [
      'Client management',
      'Project linking',
      'Contact tracking',
      'Communication history',
      'Analytics'
    ],
    route: '/clients',
    color: 'from-teal-500 to-cyan-500',
    stats: [
      { label: 'Active', value: '12' },
      { label: 'Projects', value: '8' }
    ]
  },
  {
    name: 'Memory Agent',
    icon: '🧠',
    description: 'RAG-powered semantic memory with context-aware responses',
    status: 'active',
    capabilities: [
      'Semantic search',
      'Vector embeddings',
      'Context retrieval',
      'Long-term memory',
      '90-day recall'
    ],
    route: '/memory',
    color: 'from-indigo-500 to-purple-500',
    stats: [
      { label: 'Memories', value: '1.2K' },
      { label: 'Accuracy', value: '95%' }
    ]
  },
  {
    name: 'Mirror Mode',
    icon: '✨',
    description: 'Learn and imitate your communication style',
    status: 'active',
    capabilities: [
      'Style learning',
      'Tone matching',
      'Phrase mimicry',
      'Brevity adaptation',
      'Personalization'
    ],
    route: '/agent-console',
    color: 'from-pink-500 to-rose-500',
    stats: [
      { label: 'Samples', value: '89' },
      { label: 'Match Rate', value: '92%' }
    ]
  },
  {
    name: 'Routine Optimizer',
    icon: '⏰',
    description: 'Monitor work patterns and suggest optimal breaks',
    status: 'active',
    capabilities: [
      'Work hour tracking',
      'Break suggestions',
      'Busy period detection',
      'Notification management',
      'Productivity insights'
    ],
    route: '/admin',
    color: 'from-yellow-500 to-orange-500',
    stats: [
      { label: 'Avg Work', value: '7.2hrs' },
      { label: 'Efficiency', value: '87%' }
    ]
  },
  {
    name: 'Notification Agent',
    icon: '🔔',
    description: 'Schedule reminders and timed notifications',
    status: 'active',
    capabilities: [
      'Timed reminders',
      'Recurring notifications',
      'Smart scheduling',
      'Priority handling',
      'Telegram integration'
    ],
    route: '/agent-console',
    color: 'from-blue-500 to-indigo-500',
    stats: [
      { label: 'Scheduled', value: '23' },
      { label: 'Delivered', value: '156' }
    ]
  }
]

export default function MultiAgentDashboard() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [agentProfile, setAgentProfile] = useState<any>(null)

  useEffect(() => {
    // Fetch agent profile from backend
    const fetchAgentProfile = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/agent/profile`)
        if (response.ok) {
          const data = await response.json()
          setAgentProfile(data)
        }
      } catch (error) {
        console.error('Error fetching agent profile:', error)
      }
    }

    fetchAgentProfile()
  }, [])

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🤖 Multi-Agent Dashboard
        </h1>
        <p className="text-gray-600">
          {agentProfile ? (
            <>
              {agentProfile.name} - {agentProfile.capabilities?.length || 0} active agents serving {agentProfile.owner}
            </>
          ) : (
            'Manage and monitor all AI agents in one place'
          )}
        </p>
      </header>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white rounded-lg p-6 shadow-md">
          <div className="text-3xl font-bold mb-2">{agents.filter(a => a.status === 'active').length}</div>
          <div className="text-blue-100">Active Agents</div>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-emerald-500 text-white rounded-lg p-6 shadow-md">
          <div className="text-3xl font-bold mb-2">
            {agents.reduce((acc, agent) => acc + (agent.capabilities?.length || 0), 0)}
          </div>
          <div className="text-green-100">Total Capabilities</div>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-pink-500 text-white rounded-lg p-6 shadow-md">
          <div className="text-3xl font-bold mb-2">24/7</div>
          <div className="text-purple-100">Uptime</div>
        </div>
        <div className="bg-gradient-to-br from-orange-500 to-red-500 text-white rounded-lg p-6 shadow-md">
          <div className="text-3xl font-bold mb-2">98.5%</div>
          <div className="text-orange-100">Success Rate</div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden cursor-pointer"
            onClick={() => setSelectedAgent(agent)}
          >
            {/* Agent Header */}
            <div className={`bg-gradient-to-r ${agent.color} p-6 text-white`}>
              <div className="flex items-center justify-between mb-4">
                <div className="text-5xl">{agent.icon}</div>
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${
                    agent.status === 'active' ? 'bg-green-400 animate-pulse' :
                    agent.status === 'idle' ? 'bg-yellow-400' : 'bg-gray-400'
                  }`}></span>
                  <span className="text-sm font-medium capitalize">{agent.status}</span>
                </div>
              </div>
              <h3 className="text-2xl font-bold mb-2">{agent.name}</h3>
              <p className="text-sm opacity-90">{agent.description}</p>
            </div>

            {/* Agent Stats */}
            {agent.stats && (
              <div className="p-4 bg-gray-50 border-b border-gray-200">
                <div className="grid grid-cols-2 gap-4">
                  {agent.stats.map((stat, i) => (
                    <div key={i}>
                      <div className="text-xs text-gray-500">{stat.label}</div>
                      <div className="text-lg font-bold text-gray-900">{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Capabilities */}
            <div className="p-4">
              <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Capabilities</div>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.slice(0, 3).map((cap, i) => (
                  <span
                    key={i}
                    className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full"
                  >
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length > 3 && (
                  <span className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded-full">
                    +{agent.capabilities.length - 3} more
                  </span>
                )}
              </div>
            </div>

            {/* Action */}
            <div className="p-4 border-t border-gray-200">
              <Link
                href={agent.route}
                className="block w-full text-center px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg hover:from-primary-700 hover:to-primary-800 transition-all"
              >
                Open Agent →
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedAgent(null)}
        >
          <div
            className="bg-white rounded-lg max-w-2xl w-full p-8 relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedAgent(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>

            <div className="flex items-center gap-4 mb-6">
              <div className="text-6xl">{selectedAgent.icon}</div>
              <div>
                <h2 className="text-3xl font-bold text-gray-900">{selectedAgent.name}</h2>
                <p className="text-gray-600">{selectedAgent.description}</p>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">All Capabilities</h3>
              <div className="grid grid-cols-1 gap-2">
                {selectedAgent.capabilities.map((cap, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-primary-600">✓</span>
                    <span className="text-gray-700">{cap}</span>
                  </div>
                ))}
              </div>
            </div>

            {selectedAgent.stats && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  {selectedAgent.stats.map((stat, i) => (
                    <div key={i} className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-500">{stat.label}</div>
                      <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Link
              href={selectedAgent.route}
              className="block w-full text-center px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg hover:from-primary-700 hover:to-primary-800 transition-all font-medium"
            >
              Open {selectedAgent.name} →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

