"use client"

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface Client {
  id: number
  name: string
  contact?: string
  email?: string
  company?: string
  business_id: number
  notes?: string
  businesses?: { name: string }
  invoices?: any[]
  created_at: string
}

interface Business {
  id: number
  name: string
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    email: '',
    company: '',
    business_id: '',
    notes: ''
  })

  useEffect(() => {
    fetchClients()
    fetchBusinesses()
  }, [])

  const fetchClients = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/client/list`)
      const data = await response.json()
      setClients(data.data || [])
    } catch (error) {
      console.error('Error fetching clients:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchBusinesses = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/finance/businesses`)
      const data = await response.json()
      setBusinesses(data.businesses || [])
    } catch (error) {
      console.error('Error fetching businesses:', error)
    }
  }

  const fetchClientDetails = async (clientId: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/client/${clientId}`)
      const data = await response.json()
      setSelectedClient(data.data)
    } catch (error) {
      console.error('Error fetching client details:', error)
    }
  }

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/client/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          business_id: parseInt(formData.business_id)
        })
      })

      if (response.ok) {
        setShowCreateForm(false)
        setFormData({ name: '', contact: '', email: '', company: '', business_id: '', notes: '' })
        fetchClients()
      }
    } catch (error) {
      console.error('Error creating client:', error)
    }
  }

  const handleDeleteClient = async (clientId: number) => {
    if (!confirm('Are you sure you want to delete this client?')) return

    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/client/${clientId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        fetchClients()
        setSelectedClient(null)
      } else {
        const data = await response.json()
        alert(data.message || 'Failed to delete client')
      }
    } catch (error) {
      console.error('Error deleting client:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return <div className="p-8">Loading clients...</div>
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Clients</h1>
        <p className="text-gray-600">Manage your business clients and contacts</p>
      </div>

      {/* Create Button */}
      <div className="flex gap-4 mb-6">
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? 'Cancel' : '+ Add Client'}
        </Button>
      </div>

      {/* Create Client Form */}
      {showCreateForm && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Client</h2>
          <form onSubmit={handleCreateClient} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Client Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="John Doe"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Business *</label>
              <select
                value={formData.business_id}
                onChange={(e) => setFormData({ ...formData, business_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="">Select business</option>
                {businesses.map((business) => (
                  <option key={business.id} value={business.id}>
                    {business.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Contact</label>
              <input
                type="text"
                value={formData.contact}
                onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="+92 300 1234567"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="client@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Company</label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Acme Corp"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                rows={2}
                placeholder="Additional notes..."
              />
            </div>

            <div className="col-span-2">
              <Button type="submit" className="w-full">
                Add Client
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Clients Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clients List */}
        <div className="lg:col-span-2">
          <Card>
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">All Clients ({clients.length})</h2>
            </div>
            <div className="divide-y">
              {clients.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No clients found. Add your first client to get started.
                </div>
              ) : (
                clients.map((client) => (
                  <div
                    key={client.id}
                    className="p-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => fetchClientDetails(client.id)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">{client.name}</h3>
                        {client.company && (
                          <p className="text-sm text-gray-600">{client.company}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          {client.businesses?.name}
                        </p>
                      </div>
                      <div className="text-right text-sm">
                        {client.contact && <p className="text-gray-600">{client.contact}</p>}
                        {client.email && <p className="text-gray-600">{client.email}</p>}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Client Details */}
        <div className="lg:col-span-1">
          {selectedClient ? (
            <Card className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-lg font-semibold">Client Details</h2>
                <Button
                  onClick={() => handleDeleteClient(selectedClient.id)}
                  size="sm"
                  variant="destructive"
                >
                  Delete
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500">Name</label>
                  <p className="font-medium">{selectedClient.name}</p>
                </div>

                {selectedClient.company && (
                  <div>
                    <label className="text-xs text-gray-500">Company</label>
                    <p>{selectedClient.company}</p>
                  </div>
                )}

                {selectedClient.contact && (
                  <div>
                    <label className="text-xs text-gray-500">Contact</label>
                    <p>{selectedClient.contact}</p>
                  </div>
                )}

                {selectedClient.email && (
                  <div>
                    <label className="text-xs text-gray-500">Email</label>
                    <p>{selectedClient.email}</p>
                  </div>
                )}

                <div>
                  <label className="text-xs text-gray-500">Business</label>
                  <p>{selectedClient.businesses?.name}</p>
                </div>

                {selectedClient.notes && (
                  <div>
                    <label className="text-xs text-gray-500">Notes</label>
                    <p className="text-sm">{selectedClient.notes}</p>
                  </div>
                )}

                <div>
                  <label className="text-xs text-gray-500">Created</label>
                  <p className="text-sm">{formatDate(selectedClient.created_at)}</p>
                </div>

                <div className="pt-4 border-t">
                  <h3 className="font-medium mb-2">Invoices</h3>
                  {selectedClient.invoices && selectedClient.invoices.length > 0 ? (
                    <div className="space-y-2">
                      {selectedClient.invoices.map((invoice: any) => (
                        <div key={invoice.id} className="text-sm flex justify-between">
                          <span>#{invoice.invoice_number}</span>
                          <span className="font-medium">{invoice.currency} {invoice.amount}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No invoices yet</p>
                  )}
                </div>
              </div>
            </Card>
          ) : (
            <Card className="p-6">
              <p className="text-gray-500 text-center">
                Select a client to view details
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

