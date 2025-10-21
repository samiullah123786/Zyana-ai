import axios, { AxiosInstance } from 'axios';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string, authToken: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authToken}`,
      },
      timeout: 30000,
    });
  }

  async submitVideoJob(metadata: any) {
    try {
      const response = await this.client.post('/agent/video/submit', {
        metadata,
        source: 'desktop_agent',
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || error.message,
      };
    }
  }

  async testConnection() {
    try {
      const response = await this.client.get('/health');
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.message,
      };
    }
  }
}

