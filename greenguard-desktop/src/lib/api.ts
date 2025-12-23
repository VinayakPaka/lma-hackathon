import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const API_BASE_URL = 'http://localhost:8000'

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().accessToken
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor for token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true
            const refreshToken = useAuthStore.getState().refreshToken
            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    })
                    const { access_token, refresh_token } = response.data
                    useAuthStore.getState().setTokens(access_token, refresh_token)
                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch {
                    useAuthStore.getState().logout()
                }
            }
        }
        return Promise.reject(error)
    }
)

// Auth API
export const authApi = {
    login: (email: string, password: string) =>
        api.post('/auth/login', { email, password }),
    register: (name: string, email: string, password: string, role: string) =>
        api.post('/auth/register', { name, email, password, role }),
    refresh: (refreshToken: string) =>
        api.post('/auth/refresh', { refresh_token: refreshToken }),
}

// Upload API
export const uploadApi = {
    uploadDocument: (file: File) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/upload/document', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },
    getDocuments: (page = 1) => api.get(`/upload/documents?page=${page}`),
    getDocument: (id: number) => api.get(`/upload/document/${id}`),
}

// ESG API (Legacy regex-based)
export const esgApi = {
    extractESG: (documentId: number) =>
        api.post(`/extract/esg/${documentId}`),
    getReports: (page = 1) => api.get(`/extract/reports?page=${page}`),
    getReport: (id: number) => api.get(`/extract/report/${id}`),
}

// AI ESG API (New AI-powered analysis)
export const aiEsgApi = {
    // AI-powered ESG extraction with Perplexity + RAG
    extractWithAI: (documentId: number, useFallback = false) =>
        api.post(`/ai-extract/ai/${documentId}?use_fallback=${useFallback}`),
    // Ask questions about a document using RAG
    askDocument: (documentId: number, question: string) =>
        api.post(`/ai-extract/ask/${documentId}`, { question }),
}

// Compliance API
export const complianceApi = {
    getScore: (reportId: number) => api.get(`/compliance/score/${reportId}`),
    getSummary: () => api.get('/compliance/summary'),
    getAlerts: () => api.get('/compliance/alerts'),
}

// KPI API
export const kpiApi = {
    benchmark: (sector: string, metric: string) =>
        api.post('/kpi/benchmark', { sector, metric }),
    getSectors: () => api.get('/kpi/sectors'),
    getMetrics: (sector: string) => api.get(`/kpi/metrics/${sector}`),
}

// Use of Proceeds API
export const proceedsApi = {
    verify: (borrowerId: number, vendorName: string, amount: number, description?: string) =>
        api.post('/use-of-proceeds/verify', {
            borrower_id: borrowerId,
            vendor_name: vendorName,
            transaction_amount: amount,
            description,
        }),
    getTransactions: () => api.get('/use-of-proceeds/transactions'),
    getSummary: () => api.get('/use-of-proceeds/summary'),
}

