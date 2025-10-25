/**
 * API client for Zyana backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ZyanaAPI {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return response.json()
  }

  // Transactions
  async getTransactions(businessId?: number) {
    const params = businessId ? `?business_id=${businessId}` : ''
    return this.request(`/finance/transactions${params}`)
  }

  async createTransaction(data: any) {
    return this.request('/finance/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Loans
  async getLoans(businessId?: number) {
    const params = businessId ? `?business_id=${businessId}` : ''
    return this.request(`/finance/loans${params}`)
  }

  // Events
  async getEvents() {
    return this.request('/calendar/events')
  }

  async createEvent(data: any) {
    return this.request('/calendar/events', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Memory search
  async searchMemory(query: string, limit: number = 5) {
    return this.request('/memory/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    })
  }

  // Agent
  async sendMessage(message: string, userId: string = '1') {
    return this.request('/webhook/message', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        message,
        platform: 'web',
      }),
    })
  }

  // Profile
  async getHabitProfile(userId: number = 1) {
    return this.request(`/profile/habits?user_id=${userId}`)
  }

  async updateHabit(key: string, value: string, userId: number = 1) {
    return this.request('/profile/habits', {
      method: 'POST',
      body: JSON.stringify({ key, value, user_id: userId }),
    })
  }

  // Businesses
  async getBusinesses() {
    return this.request('/finance/businesses')
  }

  async getBusinessBySlug(slug: string) {
    const businesses = await this.request('/finance/businesses')
    return businesses.find((b: any) => b.slug === slug)
  }

  async getBusinessSummary(businessId: number, startDate?: string, endDate?: string) {
    let url = `/finance/summary/${businessId}`
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    if (params.toString()) url += `?${params.toString()}`
    return this.request(url)
  }

  // Analytics
  async getMonthlyTrend(businessId?: number, months: number = 6) {
    const params = new URLSearchParams()
    if (businessId) params.append('business_id', businessId.toString())
    params.append('months', months.toString())
    return this.request(`/finance/analytics/monthly-trend?${params.toString()}`)
  }

  async getCategoryBreakdown(businessId?: number, type: 'income' | 'expense' = 'income') {
    const params = new URLSearchParams()
    if (businessId) params.append('business_id', businessId.toString())
    params.append('type', type)
    return this.request(`/finance/analytics/by-category?${params.toString()}`)
  }

  async getRecentActivities(businessId?: number, limit: number = 10) {
    const params = new URLSearchParams()
    if (businessId) params.append('business_id', businessId.toString())
    params.append('limit', limit.toString())
    return this.request(`/finance/analytics/recent-activities?${params.toString()}`)
  }

  async getBusinessPerformance() {
    return this.request('/finance/analytics/business-performance')
  }

  // Dashboard Stats
  async getDashboardStats() {
    return this.request('/finance/analytics/dashboard-stats')
  }

  async getBusinessStats(businessId: number) {
    return this.request(`/finance/analytics/business-stats/${businessId}`)
  }
}

export const api = new ZyanaAPI()
export default api

