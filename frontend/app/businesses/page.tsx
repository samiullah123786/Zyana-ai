'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { 
  Building2, 
  Plus, 
  Edit, 
  Trash2, 
  DollarSign,
  TrendingUp,
  ArrowLeft,
  Save,
  X
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency } from '@/lib/utils'

interface Business {
  id: number
  name: string
  slug: string
  type: string
  description?: string
  balance: number
  revenue: number
  expenses: number
}

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingBusiness, setEditingBusiness] = useState<Business | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    fetchBusinesses()
  }, [])

  const fetchBusinesses = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/finance/businesses`)
      
      if (response.ok) {
        const data = await response.json()
        setBusinesses(data || [])
      }
    } catch (error) {
      console.error('Error fetching businesses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this business? All associated transactions will be deleted.')) {
      return
    }

    setDeletingId(id)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/finance/businesses/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        await fetchBusinesses()
        alert('✅ Business deleted successfully!')
      } else {
        alert('❌ Failed to delete business')
      }
    } catch (error) {
      console.error('Error deleting business:', error)
      alert('❌ Error deleting business')
    } finally {
      setDeletingId(null)
    }
  }

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
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Manage Businesses</h1>
              <p className="text-gray-600 mt-2">Create, edit, and manage all your businesses</p>
            </div>
            <Button 
              onClick={() => setShowAddModal(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Business
            </Button>
          </div>
        </div>

        {/* Businesses Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading businesses...</p>
          </div>
        ) : businesses.length === 0 ? (
          <Card>
            <CardContent className="text-center py-16">
              <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Businesses Yet</h3>
              <p className="text-gray-600 mb-6">Start by adding your first business</p>
              <Button onClick={() => setShowAddModal(true)} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Business
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {businesses.map((business) => (
              <Card key={business.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl">
                        {business.name[0]}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{business.name}</CardTitle>
                        <Badge variant="outline" className="mt-1">{business.type}</Badge>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Balance</span>
                      <span className="font-semibold text-lg">{formatCurrency(business.balance)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Revenue</span>
                      <span className="text-green-600 font-medium">{formatCurrency(business.revenue)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Expenses</span>
                      <span className="text-red-600 font-medium">{formatCurrency(business.expenses)}</span>
                    </div>
                    
                    {business.description && (
                      <p className="text-sm text-gray-600 pt-3 border-t">{business.description}</p>
                    )}

                    <div className="flex space-x-2 pt-3">
                      <Link href={`/business/${business.slug}`} className="flex-1">
                        <Button variant="outline" className="w-full" size="sm">
                          <TrendingUp className="w-4 h-4 mr-2" />
                          View Details
                        </Button>
                      </Link>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setEditingBusiness(business)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleDelete(business.id)}
                        disabled={deletingId === business.id}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        {deletingId === business.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {(showAddModal || editingBusiness) && (
        <BusinessModal
          business={editingBusiness}
          onClose={() => {
            setShowAddModal(false)
            setEditingBusiness(null)
          }}
          onSuccess={() => {
            fetchBusinesses()
            setShowAddModal(false)
            setEditingBusiness(null)
          }}
        />
      )}
    </div>
  )
}

function BusinessModal({ 
  business, 
  onClose, 
  onSuccess 
}: { 
  business: Business | null
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    name: business?.name || '',
    slug: business?.slug || '',
    type: business?.type || 'general',
    description: business?.description || ''
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      if (business) {
        // Update existing business
        const response = await fetch(
          `${apiUrl}/finance/businesses/${business.id}?name=${encodeURIComponent(formData.name)}&type=${encodeURIComponent(formData.type)}&description=${encodeURIComponent(formData.description)}`,
          { method: 'PUT' }
        )
        
        if (response.ok) {
          alert('✅ Business updated successfully!')
          onSuccess()
        } else {
          alert('❌ Failed to update business')
        }
      } else {
        // Create new business
        const response = await fetch(
          `${apiUrl}/finance/businesses?name=${encodeURIComponent(formData.name)}&slug=${encodeURIComponent(formData.slug)}&type=${encodeURIComponent(formData.type)}&description=${encodeURIComponent(formData.description)}`,
          { method: 'POST' }
        )
        
        if (response.ok) {
          alert('✅ Business created successfully!')
          onSuccess()
        } else {
          const error = await response.json()
          alert(`❌ Failed to create business: ${error.detail || 'Unknown error'}`)
        }
      }
    } catch (error) {
      console.error('Error saving business:', error)
      alert('❌ Error saving business')
    } finally {
      setSaving(false)
    }
  }

  const generateSlug = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-[120] flex items-center justify-center p-4 animate-fade-in">
      <Card className="w-full max-w-md animate-slide-up">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{business ? 'Edit Business' : 'Add New Business'}</CardTitle>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => {
                  setFormData({ 
                    ...formData, 
                    name: e.target.value,
                    slug: business ? formData.slug : generateSlug(e.target.value)
                  })
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Vidify"
              />
            </div>

            {!business && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Slug (URL) *
                </label>
                <input
                  type="text"
                  required
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., vidify"
                />
                <p className="text-xs text-gray-500 mt-1">Used in URLs, lowercase with hyphens</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="general">General</option>
                <option value="video_production">Video Production</option>
                <option value="dairy">Dairy</option>
                <option value="logistics">Logistics</option>
                <option value="retail">Retail</option>
                <option value="services">Services</option>
                <option value="other">Other</option>
              </select>
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
                placeholder="Brief description of your business..."
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
                    {business ? 'Update' : 'Create'}
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

