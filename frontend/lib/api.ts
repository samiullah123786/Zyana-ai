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
}

export const api = new ZyanaAPI()
export default api

