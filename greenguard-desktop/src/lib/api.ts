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

// KPI API (Static Benchmarks - Read Only)
export const kpiApi = {
    benchmark: (sector: string, metric: string) =>
        api.get(`/kpi/benchmark/${sector}/${metric}`),
    getSectors: () => api.get('/kpi/sectors'),
    getMetrics: (sector: string) => api.get(`/kpi/metrics/${sector}`),
}

// KPI Evaluation API (Full Banker Workflow)
export const kpiEvaluationApi = {
    // Create a new KPI evaluation
    create: (data: {
        loan_reference_id: string
        company_name: string
        industry_sector: string
        region: string
        metric: string
        target_value: number
        target_unit: string
        timeline_start_year: number
        timeline_end_year: number
        baseline_value: number
        baseline_unit: string
        baseline_year: number
        baseline_verification: string
        company_size_proxy?: string
        emissions_scope?: string
        methodology?: string
        capex_budget?: string
        plan_description?: string
        csrd_reporting_status?: string
    }) => api.post('/kpi/evaluations', data),

    // List all evaluations for current user
    list: () => api.get('/kpi/evaluations'),

    // Get single evaluation details
    get: (evaluationId: number) => api.get(`/kpi/evaluations/${evaluationId}`),

    // Attach documents to evaluation
    attachDocuments: (evaluationId: number, files: File[]) => {
        const formData = new FormData()
        files.forEach(file => formData.append('files', file))
        return api.post(`/kpi/evaluations/${evaluationId}/documents`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },

    // Run verification pipeline
    run: (evaluationId: number) => api.post(`/kpi/evaluations/${evaluationId}/run`),

    // Submit banker decision
    submitDecision: (evaluationId: number, decision: string, overrideReason?: string) =>
        api.post(`/kpi/evaluations/${evaluationId}/decision`, {
            decision,
            override_reason: overrideReason,
        }),
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

// KPI Benchmarking Engine API (New comprehensive system)
export const kpiBenchmarkApi = {
    // Get SBTi dataset statistics
    getStats: () => api.get('/kpi-benchmark/sbti/stats'),

    // Get available sectors for peer selection
    getSectors: () => api.get('/kpi-benchmark/sbti/sectors'),

    // Get available regions
    getRegions: () => api.get('/kpi-benchmark/sbti/regions'),

    // Check if company has SBTi commitment
    checkSbtiCommitment: (companyName: string) =>
        api.get(`/kpi-benchmark/sbti/check/${encodeURIComponent(companyName)}`),

    // Get peer percentiles for benchmarking
    getPeerBenchmark: (data: { sector: string; scope: string; region?: string }) =>
        api.post('/kpi-benchmark/peers/benchmark', data),

    // Classify target ambition
    classifyAmbition: (data: {
        target_percentage: number;
        sector: string;
        scope: string;
        sbti_aligned?: boolean;
        region?: string
    }) => api.post('/kpi-benchmark/ambition/classify', data),

    // Get ESG risk context from Yahoo Finance
    getEsgRisk: (ticker: string) => api.get(`/kpi-benchmark/esg/${ticker}`),

    // Check regulatory compliance
    checkCompliance: (data: {
        loan_type: string;
        metric: string;
        target_value: number;
        ambition_classification?: string;
        margin_adjustment_bps?: number;
    }) => api.post('/kpi-benchmark/compliance/check', data),

    // Get document types (mandatory vs optional)
    getDocumentTypes: () => api.get('/kpi-benchmark/document-types'),

    // Run full evaluation with documents
    evaluate: (data: {
        company_name: string;
        industry_sector: string;
        metric: string;
        target_value: number;
        target_unit: string;
        baseline_value: number;
        baseline_year: number;
        timeline_end_year: number;
        emissions_scope: string;
        ticker?: string;
        lei?: string;
        region?: string;
        facility_amount?: string;
        tenor_years?: number;
        margin_adjustment_bps?: number;
        loan_type?: string;
        documents?: Array<{ document_id: number; document_type: string; is_primary: boolean }>;
    }) => api.post('/kpi-benchmark/evaluate', data),

    // Get evaluation as PDF
    evaluatePdf: (data: {
        company_name: string;
        industry_sector: string;
        metric: string;
        target_value: number;
        target_unit: string;
        baseline_value: number;
        baseline_year: number;
        timeline_end_year: number;
        emissions_scope: string;
        ticker?: string;
        documents?: Array<{ document_id: number; document_type: string; is_primary: boolean }>;
    }) => api.post('/kpi-benchmark/evaluate/pdf', data, { responseType: 'blob' }),

    // Get executive summary only
    getExecutiveSummary: (data: {
        company_name: string;
        industry_sector: string;
        metric: string;
        target_value: number;
        target_unit: string;
        baseline_value: number;
        baseline_year: number;
        timeline_end_year: number;
        emissions_scope: string;
    }) => api.post('/kpi-benchmark/evaluate/summary', data),
}

