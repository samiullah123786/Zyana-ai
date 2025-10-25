"use client"

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface Invoice {
  id: number
  invoice_number: string
  client_id: number
  business_id: number
  amount: number
  currency: string
  due_date: string
  status: 'pending' | 'paid' | 'overdue' | 'cancelled'
  payment_date?: string
  notes?: string
  clients?: { name: string; contact?: string }
  businesses?: { name: string }
  created_at: string
}

interface Client {
  id: number
  name: string
  company?: string
}

interface Business {
  id: number
  name: string
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterBusiness, setFilterBusiness] = useState<string>('all')
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    client_id: '',
    business_id: '',
    amount: '',
    due_date: '',
    notes: ''
  })

  useEffect(() => {
    fetchInvoices()
    fetchClients()
    fetchBusinesses()
  }, [filterStatus, filterBusiness])

  const fetchInvoices = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      let url = `${API_URL}/invoice/list`
      const params = new URLSearchParams()
      
      if (filterStatus !== 'all') params.append('status', filterStatus)
      if (filterBusiness !== 'all') params.append('business_id', filterBusiness)
      
      if (params.toString()) url += `?${params.toString()}`

      const response = await fetch(url)
      const data = await response.json()
      setInvoices(data.data || [])
    } catch (error) {
      console.error('Error fetching invoices:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchClients = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/client/list`)
      const data = await response.json()
      setClients(data.data || [])
    } catch (error) {
      console.error('Error fetching clients:', error)
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

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/invoice/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: parseInt(formData.client_id),
          business_id: parseInt(formData.business_id),
          amount: parseFloat(formData.amount),
          due_date: formData.due_date,
          notes: formData.notes
        })
      })

      if (response.ok) {
        setShowCreateForm(false)
        setFormData({ client_id: '', business_id: '', amount: '', due_date: '', notes: '' })
        fetchInvoices()
      }
    } catch (error) {
      console.error('Error creating invoice:', error)
    }
  }

  const handleMarkPaid = async (invoiceId: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/invoice/${invoiceId}/pay`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_date: new Date().toISOString().split('T')[0] })
      })

      if (response.ok) {
        fetchInvoices()
      }
    } catch (error) {
      console.error('Error marking invoice as paid:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      paid: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      overdue: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800'
    }
    return styles[status as keyof typeof styles] || styles.pending
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatCurrency = (amount: number, currency: string = 'PKR') => {
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  if (loading) {
    return <div className="p-8">Loading invoices...</div>
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Invoices</h1>
        <p className="text-gray-600">Manage client invoices and track payments</p>
      </div>

      {/* Filters and Create Button */}
      <div className="flex gap-4 mb-6">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 border rounded-md"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
        </select>

        <select
          value={filterBusiness}
          onChange={(e) => setFilterBusiness(e.target.value)}
          className="px-4 py-2 border rounded-md"
        >
          <option value="all">All Businesses</option>
          {businesses.map((business) => (
            <option key={business.id} value={business.id.toString()}>
              {business.name}
            </option>
          ))}
        </select>

        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="ml-auto">
          {showCreateForm ? 'Cancel' : '+ Create Invoice'}
        </Button>
      </div>

      {/* Create Invoice Form */}
      {showCreateForm && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Create New Invoice</h2>
          <form onSubmit={handleCreateInvoice} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Client</label>
              <select
                value={formData.client_id}
                onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="">Select client</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name} {client.company && `(${client.company})`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Business</label>
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
              <label className="block text-sm font-medium mb-1">Amount</label>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="10000"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Notes (optional)</label>
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
                Create Invoice
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Invoices Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Business</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    No invoices found. Create your first invoice to get started.
                  </td>
                </tr>
              ) : (
                invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium">{invoice.invoice_number}</td>
                    <td className="px-6 py-4 text-sm">
                      {invoice.clients?.name || 'Unknown'}
                      {invoice.clients?.contact && (
                        <div className="text-xs text-gray-500">{invoice.clients.contact}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">{invoice.businesses?.name || 'Unknown'}</td>
                    <td className="px-6 py-4 text-sm font-medium">
                      {formatCurrency(invoice.amount, invoice.currency)}
                    </td>
                    <td className="px-6 py-4 text-sm">{formatDate(invoice.due_date)}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(invoice.status)}`}>
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {invoice.status === 'pending' || invoice.status === 'overdue' ? (
                        <Button
                          onClick={() => handleMarkPaid(invoice.id)}
                          size="sm"
                          variant="outline"
                        >
                          Mark Paid
                        </Button>
                      ) : invoice.status === 'paid' ? (
                        <span className="text-xs text-gray-500">
                          Paid on {invoice.payment_date && formatDate(invoice.payment_date)}
                        </span>
                      ) : null}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

