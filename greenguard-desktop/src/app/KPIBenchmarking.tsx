import { useEffect, useState, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { kpiBenchmarkApi, uploadApi } from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import {
    Loader2, Target, TrendingUp, FileText, Upload,
    CheckCircle2, XCircle, AlertTriangle, ChevronRight, Download,
    Building2, Shield, Users, Globe, Award,
    Sparkles, ArrowRight, FileUp, Trash2, Zap, BarChart3,
    TrendingDown, CheckCircle, AlertCircle, ExternalLink, History, Clock
} from 'lucide-react'
import ReportChat from '@/components/ReportChat'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    LineChart, Line, RadialBarChart, RadialBar, PolarAngleAxis
} from 'recharts'

// Helper to read/write URL params for persistence
const getEvaluationIdFromUrl = (): number | null => {
    const params = new URLSearchParams(window.location.search)
    const id = params.get('evaluation')
    return id ? parseInt(id, 10) : null
}

const setEvaluationIdInUrl = (id: number | null) => {
    const url = new URL(window.location.href)
    if (id) {
        url.searchParams.set('evaluation', id.toString())
    } else {
        url.searchParams.delete('evaluation')
    }
    window.history.replaceState({}, '', url.toString())
}

// Types
interface HistoryItem {
    id: number
    loan_reference_id: string
    company_name: string
    industry_sector: string
    metric: string
    target_value: number
    target_unit: string
    timeline_end_year: number
    status: string
    assessment_grade: string
    banker_decision: string
    created_at: string
}

type DetailedReport = {
    meta?: {
        report_title?: string
        prepared_for?: string
        prepared_by?: string
        as_of_date?: string
        version?: string
    }
    inputs_summary?: {
        company_name?: string
        industry_sector?: string
        loan_type?: string
        kpi?: {
            metric?: string
            target_value?: number
            target_unit?: string
            baseline_value?: number
            baseline_year?: number
            target_year?: number
            emissions_scope?: string
        }
    }
    data_quality?: {
        documents_reviewed?: Array<{ document_type: string; status: string; notes?: string }>
        evidence_gaps?: string[]
        confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | string
    }
    sections?: Array<{
        id: string
        title: string
        markdown?: string
        bullets?: string[]
        evidence?: Array<{ source: string; reference: string; snippet?: string }>
    }>
    figures?: Array<{
        id: string
        title: string
        type: 'bar' | 'line' | 'gauge' | string
        data: any
    }>
    risk_register?: Array<{
        id: string
        severity: string
        theme: string
        description: string
        mitigant?: string
        covenant_or_condition?: string
    }>
    recommended_terms?: {
        decision?: string
        conditions?: string[]
        monitoring_plan?: string[]
        covenants?: string[]
    }
}

interface EvaluationResult {
    report_header: {
        company_name: string
        deal_details: {
            loan_type: string
            margin_adjustment_bps?: number
        }
        analysis_date: string
    }
    executive_summary: {
        overall_recommendation: string
        recommendation_rationale: string
        key_findings?: Array<{ category: string; assessment: string; detail: string }>
        conditions_for_approval?: string[]
        ai_narrative?: string
    }
    peer_benchmarking?: {
        peer_statistics?: { peer_count?: number; confidence_level?: string; percentiles?: { median?: number; p75?: number } }
        company_position?: { percentile_rank?: number; classification?: string }
        ambition_classification?: { level?: string; rationale?: string; ai_detailed_analysis?: string; classification_explanation?: string }
        recommendation?: { action?: string; suggested_minimum?: number; message?: string }
    }
    achievability_assessment?: {
        credibility_level?: string
        signals?: Record<string, { detected: boolean; evidence?: string }>
        gaps?: Array<{ signal: string; recommendation: string }>
        ai_detailed_analysis?: string
    }
    risk_flags?: Array<{ severity: string; category: string; issue: string; recommendation: string }>
    regulatory_compliance?: { summary?: Record<string, boolean> }
    visuals?: {
        peer_comparison?: { labels?: string[]; dataset?: { label: string; data: number[] }[] }
        emissions_trajectory?: { labels?: string[]; data?: number[] }
    }
    final_decision?: { recommendation?: string; confidence?: string; conditions?: Array<{ condition: string; detail: string; priority: string }> }
    detailed_report?: DetailedReport
}

interface UploadedDocument {
    id: number
    filename: string
    document_type: string
    is_primary: boolean
    status: 'uploading' | 'processing' | 'ready' | 'error'
}

const DOCUMENT_TYPES = [
    { value: 'csrd_report', label: 'CSRD / Sustainability Report', icon: FileText, color: 'emerald', mandatory: true },
    { value: 'spts', label: 'SPTs Document', icon: Target, color: 'blue', mandatory: true },
    { value: 'spo', label: 'Second Party Opinion', icon: Award, color: 'purple', mandatory: false },
    { value: 'transition_plan', label: 'Transition Plan', icon: TrendingUp, color: 'amber', mandatory: false },
]

const INDUSTRY_SECTORS = [
    // Primary Industries
    'Agriculture, Forestry & Fishing',
    'Mining & Quarrying',
    // Manufacturing
    'Food & Beverage Manufacturing',
    'Textile & Apparel Manufacturing',
    'Wood, Paper & Printing',
    'Chemicals & Pharmaceuticals',
    'Rubber & Plastics',
    'Non-Metallic Minerals (Cement, Glass)',
    'Metals & Metal Products',
    'Electrical Equipment & Machinery',
    'Automotive & Transport Equipment',
    'Electronics & Computers',
    'Other Manufacturing',
    // Energy & Utilities
    'Oil & Gas',
    'Electricity Generation',
    'Renewable Energy',
    'Water & Waste Management',
    'Utilities',
    // Construction & Real Estate
    'Construction',
    'Real Estate',
    // Services
    'Wholesale & Retail Trade',
    'Transportation & Logistics',
    'Accommodation & Food Services',
    'Information & Communication',
    'Technology & Software',
    'Financial Services & Insurance',
    'Professional Services',
    'Healthcare & Pharmaceuticals',
    'Education',
    'Public Administration',
    // Other
    'Conglomerates',
    'Other'
]

// All EU + EEA + UK countries
const EU_COUNTRIES = [
    { code: 'AT', name: 'Austria' },
    { code: 'BE', name: 'Belgium' },
    { code: 'BG', name: 'Bulgaria' },
    { code: 'HR', name: 'Croatia' },
    { code: 'CY', name: 'Cyprus' },
    { code: 'CZ', name: 'Czech Republic' },
    { code: 'DK', name: 'Denmark' },
    { code: 'EE', name: 'Estonia' },
    { code: 'FI', name: 'Finland' },
    { code: 'FR', name: 'France' },
    { code: 'DE', name: 'Germany' },
    { code: 'GR', name: 'Greece' },
    { code: 'HU', name: 'Hungary' },
    { code: 'IE', name: 'Ireland' },
    { code: 'IT', name: 'Italy' },
    { code: 'LV', name: 'Latvia' },
    { code: 'LT', name: 'Lithuania' },
    { code: 'LU', name: 'Luxembourg' },
    { code: 'MT', name: 'Malta' },
    { code: 'NL', name: 'Netherlands' },
    { code: 'PL', name: 'Poland' },
    { code: 'PT', name: 'Portugal' },
    { code: 'RO', name: 'Romania' },
    { code: 'SK', name: 'Slovakia' },
    { code: 'SI', name: 'Slovenia' },
    { code: 'ES', name: 'Spain' },
    { code: 'SE', name: 'Sweden' },
    // EEA Countries
    { code: 'IS', name: 'Iceland' },
    { code: 'LI', name: 'Liechtenstein' },
    { code: 'NO', name: 'Norway' },
    // UK (still relevant for many ESG frameworks)
    { code: 'GB', name: 'United Kingdom' },
    // Switzerland (closely aligned with EU regulations)
    { code: 'CH', name: 'Switzerland' },
]

export default function KPIBenchmarking() {
    const [step, setStep] = useState(1)
    const [showHistory, setShowHistory] = useState(false)
    const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
    const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null)
    const [currentEvaluationId, setCurrentEvaluationId] = useState<number | null>(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [runError, setRunError] = useState<string | null>(null)
    const [reportView, setReportView] = useState<'memo' | 'highlights'>('memo')
    const [activeSectionId, setActiveSectionId] = useState<string>('executive_summary')

    // Fetch history data
    const { data: historyData, refetch: refetchHistory, isLoading: isLoadingHistory } = useQuery({
        queryKey: ['evaluation-history'],
        queryFn: () => kpiBenchmarkApi.getHistory({ limit: 20 }),
        enabled: showHistory,
    })

    // Load saved evaluation mutation
    const loadEvaluationMutation = useMutation({
        mutationFn: (evaluationId: number) => kpiBenchmarkApi.getEvaluationById(evaluationId),
        onSuccess: (response) => {
            console.log('Loaded evaluation response:', response.data)
            if (response.data?.result) {
                setEvaluationResult(response.data.result)
                const evalId = response.data.evaluation?.id || null
                setCurrentEvaluationId(evalId)
                // Persist evaluation ID in URL so it survives page reload
                setEvaluationIdInUrl(evalId)
                setShowHistory(false)
                setStep(3)
            } else {
                console.error('No result in evaluation response:', response.data)
                setRunError('Failed to load evaluation: No result data found')
            }
        },
        onError: (error: Error) => {
            console.error('Failed to load evaluation:', error)
            setRunError(`Failed to load evaluation: ${error.message}`)
            // Clear URL param on error
            setEvaluationIdInUrl(null)
        }
    })

    // Load evaluation from URL on initial mount (handles page reload)
    useEffect(() => {
        const evalIdFromUrl = getEvaluationIdFromUrl()
        if (evalIdFromUrl && !evaluationResult && !loadEvaluationMutation.isPending) {
            console.log('Loading evaluation from URL:', evalIdFromUrl)
            loadEvaluationMutation.mutate(evalIdFromUrl)
        }
    }, []) // Empty deps - only run on mount

    useEffect(() => {
        const firstSectionId = evaluationResult?.detailed_report?.sections?.[0]?.id
        if (firstSectionId) setActiveSectionId(firstSectionId)
    }, [evaluationResult])
    const [formData, setFormData] = useState({
        company_name: '',
        industry_sector: '',
        country_code: '',
        nace_code: '',
        target_emissions: '',
        baseline_value: '',
        baseline_year: 2023,
        timeline_end_year: 2030,
        emissions_scope: 'Scope 1+2',
        loan_type: 'Sustainability-Linked Loan',
    })

    const baselineEmissions = Number.parseFloat(String(formData.baseline_value || ''))
    const targetEmissions = Number.parseFloat(String(formData.target_emissions || ''))
    const hasValidBaseline = Number.isFinite(baselineEmissions) && baselineEmissions > 0
    const hasValidTarget = Number.isFinite(targetEmissions) && targetEmissions >= 0
    const computedReductionPct =
        hasValidBaseline && hasValidTarget
            ? ((baselineEmissions - targetEmissions) / baselineEmissions) * 100
            : NaN

    const readyDocs = uploadedDocs.filter(d => d.id && d.status === 'ready')
    const canRunAssessment = Boolean(
        formData.company_name.trim() &&
        formData.industry_sector.trim() &&
        formData.country_code.trim().length === 2 &&
        formData.nace_code.trim() &&
        formData.target_emissions &&
        formData.baseline_value &&
        formData.timeline_end_year >= 2025 &&
        readyDocs.length > 0
    )

    const { data: statsData } = useQuery({
        queryKey: ['sbti-stats'],
        queryFn: () => kpiBenchmarkApi.getStats(),
    })

    const uploadMutation = useMutation({
        mutationFn: (file: File) => uploadApi.uploadDocument(file),
        onSuccess: (response, file) => {
            setUploadedDocs(prev => prev.map(doc =>
                // Backend returns { id: number, ... }
                doc.filename === file.name ? { ...doc, id: response.data.id, status: 'ready' as const } : doc
            ))
        },
        onError: (_error, file) => {
            setUploadedDocs(prev => prev.map(doc =>
                doc.filename === file.name ? { ...doc, status: 'error' as const } : doc
            ))
        },
    })

    const evaluateMutation = useMutation({
        mutationFn: () => {
            const documents = uploadedDocs.filter(d => d.id && d.status === 'ready').map(d => ({
                document_id: d.id,
                document_type: d.document_type,
                is_primary: d.is_primary,
            }))
            if (!canRunAssessment) return Promise.reject(new Error('Missing required inputs or at least one uploaded document.'))
            return kpiBenchmarkApi.evaluate({
                company_name: formData.company_name,
                industry_sector: formData.industry_sector,
                country_code: formData.country_code,
                nace_code: formData.nace_code,
                metric: 'GHG Emissions Reduction',
                target_value: Number.isFinite(computedReductionPct) ? computedReductionPct : 0,
                target_unit: '%',
                baseline_value: parseFloat(formData.baseline_value),
                baseline_year: formData.baseline_year,
                timeline_end_year: formData.timeline_end_year,
                emissions_scope: formData.emissions_scope,
                loan_type: formData.loan_type,
                documents,
            })
        },
        onSuccess: (response) => {
            setEvaluationResult(response.data)
            // Capture evaluation ID for PDF generation without re-running
            if (response.data?.evaluation_id) {
                setCurrentEvaluationId(response.data.evaluation_id)
                // Persist in URL so page reload works
                setEvaluationIdInUrl(response.data.evaluation_id)
            }
            // Check if save failed (backend still returns result but with save_error)
            if (response.data?.save_error) {
                console.warn('Evaluation completed but failed to save:', response.data.save_error)
                setRunError(`Warning: Report generated but may not persist. Error: ${response.data.save_error}`)
            }
            setIsAnalyzing(false)
            setStep(3)
        },
        onError: (err: any) => {
            const msg =
                err?.response?.data?.detail ||
                err?.message ||
                'AI assessment failed. Please check inputs and try again.'
            setRunError(msg)
            setIsAnalyzing(false)
        },
    })

    const pdfMutation = useMutation({
        mutationFn: () => {
            // If we have a saved evaluation ID, use it to generate PDF without re-running
            if (currentEvaluationId) {
                return kpiBenchmarkApi.getPdfFromSaved(currentEvaluationId)
            }
            // Fallback: Run full evaluation (only for cases where no saved ID exists)
            const documents = uploadedDocs.filter(d => d.id && d.status === 'ready').map(d => ({
                document_id: d.id,
                document_type: d.document_type,
                is_primary: d.is_primary,
            }))
            if (!canRunAssessment) return Promise.reject(new Error('Missing required inputs or at least one uploaded document.'))
            return kpiBenchmarkApi.evaluatePdf({
                company_name: formData.company_name,
                industry_sector: formData.industry_sector,
                country_code: formData.country_code,
                nace_code: formData.nace_code,
                metric: 'GHG Emissions Reduction',
                target_value: Number.isFinite(computedReductionPct) ? computedReductionPct : 0,
                target_unit: '%',
                baseline_value: parseFloat(formData.baseline_value),
                baseline_year: formData.baseline_year,
                timeline_end_year: formData.timeline_end_year,
                emissions_scope: formData.emissions_scope,
                documents,
            })
        },
        onSuccess: (response) => {
            const blob = new Blob([response.data], { type: 'application/pdf' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `KPI_Assessment_${formData.company_name || 'Company'}_${new Date().toISOString().slice(0, 10)}.pdf`
            document.body.appendChild(a)
            a.click()
            a.remove()
            URL.revokeObjectURL(url)
        },
    })

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, docType: string) => {
        const files = e.target.files
        if (files && files[0]) {
            const file = files[0]
            const newDoc: UploadedDocument = {
                id: 0,
                filename: file.name,
                document_type: docType,
                is_primary: uploadedDocs.length === 0,
                status: 'uploading'
            }
            setUploadedDocs(prev => [...prev, newDoc])
            uploadMutation.mutate(file)
        }
    }

    const removeDocument = (filename: string) => {
        setUploadedDocs(prev => prev.filter(d => d.filename !== filename))
    }

    const startAnalysis = () => {
        setRunError(null)
        setIsAnalyzing(true)
        // Clear any old evaluation from URL before starting new one
        setEvaluationIdInUrl(null)
        evaluateMutation.mutate()
    }

    // Reset to start a new assessment
    const startNewAssessment = useCallback(() => {
        setStep(1)
        setEvaluationResult(null)
        setCurrentEvaluationId(null)
        setEvaluationIdInUrl(null)
        setRunError(null)
        setUploadedDocs([])
        setShowHistory(false)
    }, [])

    const canProceed =
        formData.company_name &&
        formData.industry_sector &&
        formData.country_code &&
        formData.nace_code &&
        formData.nace_code &&
        formData.target_emissions &&
        formData.baseline_value &&
        formData.timeline_end_year >= 2025

    // Show loading state when loading evaluation from URL
    if (loadEvaluationMutation.isPending) {
        return (
            <div className="min-h-screen bg-[#0a0f1a] text-white flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-emerald-400 animate-spin mx-auto mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Loading Evaluation</h2>
                    <p className="text-gray-400">Please wait while we retrieve your saved report...</p>
                </div>
            </div>
        )
    }

    // History View
    if (showHistory) {
        const historyItems: HistoryItem[] = historyData?.data?.evaluations || []
        return (
            <div className="min-h-screen bg-[#0a0f1a] text-white">
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto px-6 py-12">
                    {/* Back Button */}
                    <button onClick={startNewAssessment} className="flex items-center gap-2 text-gray-400 hover:text-white mb-8 transition-colors">
                        <ChevronRight className="w-5 h-5 rotate-180" />
                        Back to New Assessment
                    </button>

                    {/* Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-400 text-sm mb-6">
                            <History className="w-4 h-4" />
                            Assessment History
                        </div>
                        <h1 className="text-4xl font-bold mb-4">Past Evaluations</h1>
                        <p className="text-gray-400 max-w-xl mx-auto">
                            View and load previously completed KPI assessments
                        </p>
                    </div>

                    {/* History List */}
                    {isLoadingHistory ? (
                        <div className="flex justify-center py-20">
                            <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                        </div>
                    ) : historyItems.length === 0 ? (
                        <div className="text-center py-20 bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl">
                            <Clock className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400 text-lg">No evaluations found</p>
                            <p className="text-gray-500 text-sm mt-2">Complete your first assessment to see it here</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {historyItems.map((item) => {
                                const isApproved = item.banker_decision === 'APPROVE' || item.banker_decision === 'CONDITIONAL_APPROVAL'
                                const gradeColor = item.assessment_grade === 'AMBITIOUS' ? 'text-green-400' :
                                    item.assessment_grade === 'MODERATE' ? 'text-amber-400' : 'text-red-400'
                                const decisionColor = isApproved ? 'bg-green-500/20 text-green-400' :
                                    item.banker_decision === 'REJECT' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'

                                return (
                                    <div
                                        key={item.id}
                                        className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6 hover:border-purple-500/30 transition-colors cursor-pointer"
                                        onClick={() => loadEvaluationMutation.mutate(item.id)}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-lg font-semibold text-white">{item.company_name}</h3>
                                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${decisionColor}`}>
                                                        {item.banker_decision?.replace(/_/g, ' ') || 'PENDING'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-4 text-sm text-gray-400">
                                                    <span>{item.industry_sector}</span>
                                                    <span>•</span>
                                                    <span>{item.target_value?.toFixed(1)}% reduction by {item.timeline_end_year}</span>
                                                    <span>•</span>
                                                    <span className={gradeColor}>{item.assessment_grade || 'N/A'}</span>
                                                </div>
                                                <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
                                                    <Clock className="w-3 h-3" />
                                                    {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString()}
                                                    <span className="ml-2 text-gray-600">Ref: {item.loan_reference_id}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        kpiBenchmarkApi.getPdfFromSaved(item.id).then(response => {
                                                            const blob = new Blob([response.data], { type: 'application/pdf' })
                                                            const url = URL.createObjectURL(blob)
                                                            const a = document.createElement('a')
                                                            a.href = url
                                                            a.download = `KPI_Assessment_${item.company_name.replace(/\s+/g, '_')}.pdf`
                                                            document.body.appendChild(a)
                                                            a.click()
                                                            a.remove()
                                                            URL.revokeObjectURL(url)
                                                        })
                                                    }}
                                                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                                                    title="Download PDF"
                                                >
                                                    <Download className="w-4 h-4 text-gray-400" />
                                                </button>
                                                <ArrowRight className="w-5 h-5 text-gray-600" />
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>
        )
    }

    // Step 1: Input Form
    if (step === 1) {
        return (
            <div className="min-h-screen bg-[#0a0f1a] text-white">
                {/* Animated Background */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto px-6 py-12">
                    {/* History Button - Top Right */}
                    <div className="flex justify-end mb-4">
                        <button
                            onClick={() => { setShowHistory(true); refetchHistory(); }}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-xl text-gray-300 hover:text-white transition-all"
                        >
                            <History className="w-4 h-4" />
                            View History
                        </button>
                    </div>

                    {/* Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm mb-6">
                            <Sparkles className="w-4 h-4" />
                            AI-Powered ESG Assessment
                        </div>
                        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-white via-emerald-200 to-emerald-400 bg-clip-text text-transparent">
                            KPI Benchmarking Engine
                        </h1>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Evaluate sustainability-linked loan targets against industry peers and science-based pathways
                        </p>
                        {statsData?.data && (
                            <div className="flex justify-center gap-8 mt-8">
                                <div className="flex items-center gap-2 text-gray-400">
                                    <Users className="w-5 h-5 text-emerald-400" />
                                    <span className="text-white font-semibold">{statsData.data.companies_count?.toLocaleString()}</span>
                                    <span>SBTi Companies</span>
                                </div>
                                <div className="flex items-center gap-2 text-gray-400">
                                    <Globe className="w-5 h-5 text-blue-400" />
                                    <span className="text-white font-semibold">{statsData.data.sectors_available || 85}</span>
                                    <span>Industry Sectors</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Main Form Card */}
                    <div className="bg-gray-900/50 backdrop-blur-xl border border-gray-800 rounded-3xl p-8 shadow-2xl">
                        <div className="grid grid-cols-2 gap-8">
                            {/* Left Column - Company Info */}
                            <div className="space-y-6">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-2 bg-emerald-500/20 rounded-lg">
                                        <Building2 className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    <h2 className="text-xl font-semibold">Borrower Information</h2>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Company Name</label>
                                    <input
                                        type="text"
                                        value={formData.company_name}
                                        onChange={(e) => setFormData(prev => ({ ...prev, company_name: e.target.value }))}
                                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                                        placeholder="e.g., Atos SE"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Industry Sector</label>
                                    <select
                                        value={formData.industry_sector}
                                        onChange={(e) => setFormData(prev => ({ ...prev, industry_sector: e.target.value }))}
                                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
                                    >
                                        <option value="">Select industry sector</option>
                                        {INDUSTRY_SECTORS.map(sector => (
                                            <option key={sector} value={sector}>{sector}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Country</label>
                                        <select
                                            value={formData.country_code}
                                            onChange={(e) =>
                                                setFormData(prev => ({ ...prev, country_code: e.target.value }))
                                            }
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
                                        >
                                            <option value="">Select Country</option>
                                            {EU_COUNTRIES.map(country => (
                                                <option key={country.code} value={country.code}>
                                                    {country.name} ({country.code})
                                                </option>
                                            ))}
                                        </select>
                                        <p className="mt-1 text-xs text-gray-500">EU, EEA, UK & Switzerland supported</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">NACE Code</label>
                                        <input
                                            type="text"
                                            value={formData.nace_code}
                                            onChange={(e) =>
                                                setFormData(prev => ({ ...prev, nace_code: e.target.value.toUpperCase().trim() }))
                                            }
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                                            placeholder="e.g., C25.11 or J62"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Loan Type</label>
                                        <input
                                            type="text"
                                            value={formData.loan_type}
                                            onChange={(e) => setFormData(prev => ({ ...prev, loan_type: e.target.value }))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-emerald-500 transition-all"
                                            placeholder="Sustainability-Linked Loan"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Right Column - KPI Details */}
                            <div className="space-y-6">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-2 bg-blue-500/20 rounded-lg">
                                        <Target className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <h2 className="text-xl font-semibold">Sustainability Target</h2>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Baseline Emissions (tCO2e)</label>
                                        <input
                                            type="number"
                                            value={formData.baseline_value}
                                            onChange={(e) => setFormData(prev => ({ ...prev, baseline_value: e.target.value }))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-blue-500 transition-all"
                                            placeholder="100000"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Baseline Year</label>
                                        <input
                                            type="number"
                                            value={formData.baseline_year}
                                            onChange={(e) => setFormData(prev => ({ ...prev, baseline_year: parseInt(e.target.value) }))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white focus:border-blue-500 transition-all"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Target Emissions (tCO2e)</label>
                                        <input
                                            type="number"
                                            value={formData.target_emissions}
                                            onChange={(e) => setFormData(prev => ({ ...prev, target_emissions: e.target.value }))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-blue-500 transition-all"
                                            placeholder="e.g., 54000"
                                        />
                                        <div className="mt-2 flex items-center justify-between text-xs">
                                            <span className="text-gray-500">Auto-calculated reduction</span>
                                            <span className={Number.isFinite(computedReductionPct) && computedReductionPct >= 0 ? 'text-emerald-300' : 'text-amber-300'}>
                                                {Number.isFinite(computedReductionPct) ? `${computedReductionPct.toFixed(1)}%` : '—'}
                                            </span>
                                        </div>
                                    </div>
                                    <div>
                                        <input
                                            type="number"
                                            value={formData.timeline_end_year}
                                            onChange={(e) => setFormData(prev => ({ ...prev, timeline_end_year: parseInt(e.target.value) }))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white focus:border-blue-500 transition-all"
                                            min="2025"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Emissions Scope</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['Scope 1+2', 'Scope 1+2+3', 'Scope 3'].map(scope => (
                                            <button
                                                key={scope}
                                                onClick={() => setFormData(prev => ({ ...prev, emissions_scope: scope }))}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${formData.emissions_scope === scope
                                                    ? 'bg-blue-500 text-white'
                                                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                    }`}
                                            >
                                                {scope}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Continue Button */}
                        <div className="mt-10 flex justify-end">
                            <button
                                onClick={() => canProceed && setStep(2)}
                                disabled={!canProceed}
                                className={`group flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all ${canProceed
                                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/25'
                                    : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                    }`}
                            >
                                Continue to Documents
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // Step 2: Document Upload
    if (step === 2) {
        return (
            <div className="min-h-screen bg-[#0a0f1a] text-white">
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto px-6 py-12">
                    {/* Back Button */}
                    <button onClick={() => setStep(1)} className="flex items-center gap-2 text-gray-400 hover:text-white mb-8 transition-colors">
                        <ChevronRight className="w-5 h-5 rotate-180" />
                        Back to Company Details
                    </button>

                    {/* Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-400 text-sm mb-6">
                            <FileUp className="w-4 h-4" />
                            Document Analysis
                        </div>
                        <h1 className="text-4xl font-bold mb-4">Upload Supporting Documents</h1>
                        <p className="text-gray-400 max-w-xl mx-auto">
                            Upload ESG reports and sustainability documents for AI-powered analysis
                        </p>
                    </div>

                    {/* Document Upload Grid */}
                    <div className="grid grid-cols-2 gap-6 mb-8">
                        {DOCUMENT_TYPES.map((docType) => {
                            const uploadedDoc = uploadedDocs.find(d => d.document_type === docType.value)
                            const Icon = docType.icon
                            const colorClasses = ({
                                emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400' },
                                blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' },
                                purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' },
                                amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400' },
                            } as const)[docType.color] || { bg: 'bg-gray-800/50', border: 'border-gray-700', text: 'text-gray-300' }

                            return (
                                <div
                                    key={docType.value}
                                    className={`relative p-6 rounded-2xl border-2 border-dashed transition-all ${uploadedDoc
                                        ? 'bg-gray-800/50 border-gray-600'
                                        : `${colorClasses.bg} ${colorClasses.border} hover:border-opacity-60`
                                        }`}
                                >
                                    {uploadedDoc ? (
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-4">
                                                <div className={`p-3 rounded-xl ${colorClasses.bg}`}>
                                                    {uploadedDoc.status === 'ready' ? (
                                                        <CheckCircle2 className="w-6 h-6 text-green-400" />
                                                    ) : uploadedDoc.status === 'uploading' ? (
                                                        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                                                    ) : (
                                                        <XCircle className="w-6 h-6 text-red-400" />
                                                    )}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-white">{docType.label}</p>
                                                    <p className="text-sm text-gray-400 truncate max-w-xs">{uploadedDoc.filename}</p>
                                                    <p className={`text-xs mt-1 ${uploadedDoc.status === 'ready' ? 'text-green-400' :
                                                        uploadedDoc.status === 'uploading' ? 'text-blue-400' : 'text-red-400'
                                                        }`}>
                                                        {uploadedDoc.status === 'ready' ? 'Ready for analysis' :
                                                            uploadedDoc.status === 'uploading' ? 'Processing...' : 'Upload failed'}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeDocument(uploadedDoc.filename)}
                                                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4 text-gray-400" />
                                            </button>
                                        </div>
                                    ) : (
                                        <label className="cursor-pointer block">
                                            <input
                                                type="file"
                                                accept=".pdf,.doc,.docx"
                                                onChange={(e) => handleFileUpload(e, docType.value)}
                                                className="hidden"
                                            />
                                            <div className="text-center">
                                                <div className={`inline-flex p-4 rounded-2xl ${colorClasses.bg} mb-4`}>
                                                    <Icon className={`w-8 h-8 ${colorClasses.text}`} />
                                                </div>
                                                <p className="font-medium text-white mb-1">{docType.label}</p>
                                                <p className="text-sm text-gray-500 mb-3">
                                                    {docType.mandatory ? (
                                                        <span className="text-amber-400">Required</span>
                                                    ) : 'Optional'}
                                                </p>
                                                <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg text-sm text-gray-400">
                                                    <Upload className="w-4 h-4" />
                                                    Click to upload
                                                </div>
                                            </div>
                                        </label>
                                    )}
                                </div>
                            )
                        })}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between">
                        <p className="text-gray-500 text-sm">
                            {uploadedDocs.filter(d => d.status === 'ready').length} document(s) ready for analysis
                        </p>
                        <button
                            onClick={startAnalysis}
                            disabled={isAnalyzing || !canRunAssessment}
                            className={`group flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all ${canRunAssessment && !isAnalyzing
                                ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/25'
                                : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                }`}
                        >
                            {isAnalyzing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing Documents...
                                </>
                            ) : (
                                <>
                                    <Zap className="w-5 h-5" />
                                    Run AI Assessment
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </div>

                    {runError && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200">
                            <p className="font-semibold mb-1">Unable to run AI assessment</p>
                            <p className="text-sm text-red-200/90">{runError}</p>
                        </div>
                    )}

                    {/* Analysis Progress */}
                    {isAnalyzing && (
                        <div className="mt-8 p-6 bg-gray-900/80 backdrop-blur border border-gray-800 rounded-2xl">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="relative">
                                    <div className="w-12 h-12 rounded-full border-4 border-purple-500/30 border-t-purple-500 animate-spin" />
                                    <Sparkles className="w-5 h-5 text-purple-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                                </div>
                                <div>
                                    <p className="font-semibold text-white">AI Assessment in Progress</p>
                                    <p className="text-sm text-gray-400">Analyzing documents with 17 specialized agents...</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {['Extracting KPIs', 'Peer Benchmarking', 'Credibility Analysis', 'Regulatory Check'].map((task, i) => (
                                    <div key={task} className="flex items-center gap-3 text-sm">
                                        <div className={`w-2 h-2 rounded-full ${i < 2 ? 'bg-green-400' : 'bg-gray-600 animate-pulse'}`} />
                                        <span className={i < 2 ? 'text-gray-300' : 'text-gray-500'}>{task}</span>
                                        {i < 2 && <CheckCircle className="w-4 h-4 text-green-400" />}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    // Step 3: Results Report
    if (step === 3 && evaluationResult) {
        const result = evaluationResult
        const memo = result.detailed_report
        const recommendation = result.final_decision?.recommendation || result.executive_summary.overall_recommendation
        const isApproved = recommendation === 'APPROVE' || recommendation === 'CONDITIONAL_APPROVAL'

        // Get target ambition from various possible sources
        const targetAmbition = result.peer_benchmarking?.ambition_classification?.level
            || (result.peer_benchmarking?.company_position?.percentile_rank ?
                (result.peer_benchmarking.company_position.percentile_rank >= 75 ? 'HIGHLY_AMBITIOUS'
                    : result.peer_benchmarking.company_position.percentile_rank >= 50 ? 'AMBITIOUS'
                        : result.peer_benchmarking.company_position.percentile_rank >= 25 ? 'MARKET_ALIGNED'
                            : 'BELOW_MARKET')
                : 'N/A')

        const getRecommendationStyle = () => {
            switch (recommendation) {
                case 'APPROVE': return { bg: 'from-green-500 to-emerald-500', text: 'text-green-400', icon: CheckCircle2 }
                case 'CONDITIONAL_APPROVAL': return { bg: 'from-amber-500 to-yellow-500', text: 'text-amber-400', icon: AlertCircle }
                case 'REJECT': return { bg: 'from-red-500 to-rose-500', text: 'text-red-400', icon: XCircle }
                default: return { bg: 'from-gray-500 to-gray-600', text: 'text-gray-400', icon: AlertTriangle }
            }
        }

        const getAmbitionStyle = () => {
            const ambition = targetAmbition?.toUpperCase()?.replace(/[_\s]/g, '_')
            if (ambition?.includes('HIGHLY') || ambition?.includes('SCIENCE')) {
                return { bg: 'from-emerald-600 to-teal-600', text: 'text-emerald-400', icon: Award }
            } else if (ambition?.includes('AMBITIOUS') || ambition?.includes('ABOVE')) {
                return { bg: 'from-blue-500 to-cyan-500', text: 'text-blue-400', icon: TrendingUp }
            } else if (ambition?.includes('MARKET') || ambition?.includes('ALIGNED')) {
                return { bg: 'from-amber-500 to-orange-500', text: 'text-amber-400', icon: Target }
            } else {
                return { bg: 'from-red-500 to-rose-500', text: 'text-red-400', icon: TrendingDown }
            }
        }

        const recStyle = getRecommendationStyle()
        const RecIcon = recStyle.icon
        const ambitionStyle = getAmbitionStyle()
        const AmbitionIcon = ambitionStyle.icon

        const fallbackCompanyPct = Number.isFinite(computedReductionPct) ? computedReductionPct : 5
        const peerChartData = (result.visuals?.peer_comparison?.labels || ['Company', 'Median', 'Top 25%']).map((label, i) => ({
            name: label,
            value: result.visuals?.peer_comparison?.dataset?.[0]?.data?.[i] || [fallbackCompanyPct, 5, 7.5][i]
        }))

        const trajectoryData = (result.visuals?.emissions_trajectory?.labels || [formData.baseline_year.toString(), '2026', formData.timeline_end_year.toString()]).map((label, i) => ({
            year: label,
            emissions: result.visuals?.emissions_trajectory?.data?.[i] || [100, 75, 50][i]
        }))

        const figures = memo?.figures || []
        const sections = memo?.sections || []
        const activeSection = sections.find(s => s.id === activeSectionId) || sections[0]

        const gaugeFigure = figures.find(f => f.type === 'gauge')
        const gaugeValue = typeof gaugeFigure?.data?.value === 'number' ? gaugeFigure?.data?.value : undefined

        return (
            <div className="min-h-screen bg-[#0a0f1a] text-white">
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className={`absolute top-0 left-0 w-full h-96 bg-gradient-to-b ${isApproved ? 'from-emerald-500/5' : 'from-amber-500/5'} to-transparent`} />
                </div>

                <div className="relative z-10 max-w-6xl mx-auto px-6 py-8">
                    {/* Report Header */}
                    <div className="flex items-start justify-between mb-8">
                        <div>
                            <p className="text-gray-500 text-sm mb-2">Assessment Report | {result.report_header.analysis_date}</p>
                            <h1 className="text-4xl font-bold mb-2">{result.report_header.company_name}</h1>
                            <p className="text-gray-400">{result.report_header.deal_details.loan_type}</p>
                        </div>
                        <button
                            onClick={() => pdfMutation.mutate()}
                            disabled={pdfMutation.isPending}
                            className="flex items-center gap-2 px-5 py-3 bg-gray-800 hover:bg-gray-700 disabled:opacity-60 rounded-xl transition-colors"
                        >
                            {pdfMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                            Export PDF
                        </button>
                    </div>

                    {/* Recommendation Hero - Two Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                        {/* Credit Recommendation Card */}
                        <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${recStyle.bg} p-6`}>
                            <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-4 mb-3">
                                    <div className="p-3 bg-white/20 rounded-xl backdrop-blur">
                                        <RecIcon className="w-8 h-8 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-white/80 text-xs font-medium uppercase tracking-wider mb-1">Credit Recommendation</p>
                                        <p className="text-2xl font-bold text-white">
                                            {recommendation?.replace(/_/g, ' ') || 'UNDER REVIEW'}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3 pt-3 border-t border-white/20">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/70 text-sm">Confidence Level</span>
                                        <span className="text-white font-semibold">{result.final_decision?.confidence || 'MEDIUM'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Target Ambition Card */}
                        <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${ambitionStyle.bg} p-6`}>
                            <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-4 mb-3">
                                    <div className="p-3 bg-white/20 rounded-xl backdrop-blur">
                                        <AmbitionIcon className="w-8 h-8 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-white/80 text-xs font-medium uppercase tracking-wider mb-1">Target Ambition</p>
                                        <p className="text-2xl font-bold text-white">
                                            {targetAmbition?.replace(/_/g, ' ') || 'ASSESSING'}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3 pt-3 border-t border-white/20">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/70 text-sm">Peer Percentile</span>
                                        <span className="text-white font-semibold">
                                            {result.peer_benchmarking?.company_position?.percentile_rank
                                                ? `${Math.round(result.peer_benchmarking.company_position.percentile_rank)}th`
                                                : 'N/A'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Executive Summary */}
                    {result.executive_summary.ai_narrative && (
                        <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6 mb-8">
                            <div className="flex items-center gap-3 mb-4">
                                <Sparkles className="w-5 h-5 text-purple-400" />
                                <h2 className="text-lg font-semibold">Detailed Assessment Report</h2>
                            </div>
                            <div className="text-gray-300 leading-relaxed prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown>{result.executive_summary.ai_narrative}</ReactMarkdown>
                            </div>
                        </div>
                    )}

                    {/* Report View Toggle */}
                    {memo && (
                        <div className="flex items-center gap-2 mb-6">
                            <button
                                onClick={() => setReportView('memo')}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${reportView === 'memo' ? 'bg-emerald-500 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                    }`}
                            >
                                Credit Memo
                            </button>
                            <button
                                onClick={() => setReportView('highlights')}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${reportView === 'highlights' ? 'bg-emerald-500 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                    }`}
                            >
                                Highlights
                            </button>
                            <div className="ml-auto text-xs text-gray-500">
                                {memo.meta?.prepared_for ? `${memo.meta.prepared_for} • ` : ''}{memo.meta?.as_of_date || result.report_header.analysis_date}
                            </div>
                        </div>
                    )}

                    {/* Report Q&A Chat */}
                    {currentEvaluationId && (
                        <div className="mb-8">
                            <ReportChat evaluationId={currentEvaluationId} />
                        </div>
                    )}

                    {/* Credit Memo (Detailed) */}
                    {memo && reportView === 'memo' && (
                        <div className="grid grid-cols-12 gap-6 mb-8">
                            <aside className="col-span-4 bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-5">
                                <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Contents</p>
                                <div className="space-y-1">
                                    {(sections || []).map((s) => (
                                        <button
                                            key={s.id}
                                            onClick={() => setActiveSectionId(s.id)}
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${activeSectionId === s.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800/60'
                                                }`}
                                        >
                                            {s.title}
                                        </button>
                                    ))}
                                    <div className="pt-3 mt-3 border-t border-gray-800">
                                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Figures</p>
                                        {(figures || []).map((f) => (
                                            <div key={f.id} className="text-sm text-gray-400 py-1">{f.title}</div>
                                        ))}
                                    </div>
                                </div>
                            </aside>

                            <section className="col-span-8 space-y-6">
                                {gaugeValue !== undefined && (
                                    <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                            <Shield className="w-5 h-5 text-purple-400" />
                                            Credibility Score (Indicative)
                                        </h3>
                                        <div className="h-56">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <RadialBarChart
                                                    innerRadius="70%"
                                                    outerRadius="100%"
                                                    data={[{ name: 'Credibility', value: gaugeValue }]}
                                                    startAngle={180}
                                                    endAngle={0}
                                                >
                                                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                                                    <RadialBar dataKey="value" cornerRadius={10} fill="#A855F7" />
                                                </RadialBarChart>
                                            </ResponsiveContainer>
                                        </div>
                                        <p className="text-center text-2xl font-bold text-white -mt-6">{Math.round(gaugeValue)} / 100</p>
                                        <p className="text-center text-sm text-gray-400">{gaugeFigure?.data?.label || result.achievability_assessment?.credibility_level || 'MEDIUM'}</p>
                                    </div>
                                )}

                                {activeSection && (
                                    <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                        <h2 className="text-xl font-semibold mb-3">{activeSection.title}</h2>
                                        {activeSection.markdown && (
                                            <div className="text-gray-300 leading-relaxed mb-4 prose prose-invert prose-sm max-w-none prose-headings:text-white prose-headings:font-semibold prose-h3:text-base prose-strong:text-white prose-p:my-2">
                                                <ReactMarkdown>{activeSection.markdown}</ReactMarkdown>
                                            </div>
                                        )}
                                        {(activeSection.bullets || []).length > 0 && (
                                            <ul className="space-y-2 text-sm text-gray-300">
                                                {(activeSection.bullets || []).map((b, idx) => (
                                                    <li key={idx} className="flex gap-2">
                                                        <span className="mt-1 w-2 h-2 rounded-full bg-emerald-400/70" />
                                                        <span>{b}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        )}

                                        {(activeSection.evidence || []).length > 0 && (
                                            <div className="mt-5 pt-5 border-t border-gray-800">
                                                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Evidence</p>
                                                <div className="space-y-2">
                                                    {(activeSection.evidence || []).map((e, idx) => (
                                                        <div key={idx} className="text-sm text-gray-400">
                                                            <span className="text-gray-300 font-medium">{e.source}</span>
                                                            <span className="text-gray-500"> • {e.reference}</span>
                                                            {e.snippet ? <div className="text-gray-500 mt-1">{e.snippet}</div> : null}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {(memo.risk_register || []).length > 0 && (
                                    <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                            <AlertTriangle className="w-5 h-5 text-red-400" />
                                            Risk Register
                                        </h3>
                                        <div className="space-y-3">
                                            {(memo.risk_register || []).slice(0, 8).map((r) => (
                                                <div key={r.id} className="p-4 bg-gray-950/40 border border-gray-800 rounded-xl">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <p className="font-semibold text-white">{r.id} • {r.theme}</p>
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${r.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' : r.severity === 'LOW' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'
                                                            }`}>{r.severity}</span>
                                                    </div>
                                                    <p className="text-sm text-gray-300">{r.description}</p>
                                                    {r.mitigant ? <p className="text-sm text-gray-500 mt-2">Mitigant: {r.mitigant}</p> : null}
                                                    {r.covenant_or_condition ? <p className="text-sm text-gray-500 mt-1">Condition/Covenant: {r.covenant_or_condition}</p> : null}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {(memo.recommended_terms?.monitoring_plan || []).length > 0 && (
                                    <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                            Monitoring Plan
                                        </h3>
                                        <ul className="space-y-2 text-sm text-gray-300">
                                            {(memo.recommended_terms?.monitoring_plan || []).map((m, idx) => (
                                                <li key={idx} className="flex gap-2">
                                                    <span className="mt-1 w-2 h-2 rounded-full bg-emerald-400/70" />
                                                    <span>{m}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </section>
                        </div>
                    )}

                    {(!memo || reportView === 'highlights') && (
                        <>
                            {/* Key Metrics Grid */}
                            <div className="grid grid-cols-4 gap-4 mb-8">
                                {(result.executive_summary.key_findings || []).slice(0, 4).map((finding, i) => (
                                    <div key={i} className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-5">
                                        <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">{finding.category}</p>
                                        <p className={`text-2xl font-bold ${finding.assessment === 'STRONG' || finding.assessment === 'HIGH' || finding.assessment === 'COMPLIANT' ? 'text-green-400' :
                                            finding.assessment === 'WEAK' || finding.assessment === 'LOW' ? 'text-red-400' : 'text-amber-400'
                                            }`}>
                                            {finding.assessment}
                                        </p>
                                        <p className="text-gray-500 text-sm mt-2 line-clamp-2">{finding.detail}</p>
                                    </div>
                                ))}
                            </div>

                            {/* Charts Row */}
                            <div className="grid grid-cols-2 gap-6 mb-8">
                                {/* Peer Comparison */}
                                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                        <BarChart3 className="w-5 h-5 text-emerald-400" />
                                        Peer Benchmarking
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={peerChartData} layout="vertical">
                                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                                <XAxis type="number" stroke="#9CA3AF" fontSize={12} unit="%" />
                                                <YAxis dataKey="name" type="category" stroke="#9CA3AF" fontSize={12} width={100} />
                                                <RechartsTooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} />
                                                <Bar dataKey="value" fill="#10B981" radius={[0, 4, 4, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div className="mt-4 flex items-center justify-between text-sm">
                                        <span className="text-gray-400">
                                            {result.peer_benchmarking?.peer_statistics?.peer_count || 5} peers analyzed
                                        </span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${result.peer_benchmarking?.ambition_classification?.level === 'SCIENCE_ALIGNED' ? 'bg-green-500/20 text-green-400' :
                                            result.peer_benchmarking?.ambition_classification?.level === 'ABOVE_MARKET' ? 'bg-blue-500/20 text-blue-400' :
                                                'bg-amber-500/20 text-amber-400'
                                            }`}>
                                            {result.peer_benchmarking?.ambition_classification?.level?.replace(/_/g, ' ') || 'MODERATE'}
                                        </span>
                                    </div>
                                </div>

                                {/* Emissions Trajectory */}
                                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                        <TrendingDown className="w-5 h-5 text-blue-400" />
                                        Emissions Trajectory
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={trajectoryData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                                <XAxis dataKey="year" stroke="#9CA3AF" fontSize={12} />
                                                <YAxis stroke="#9CA3AF" fontSize={12} unit="%" />
                                                <RechartsTooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} />
                                                <Line type="monotone" dataKey="emissions" stroke="#3B82F6" strokeWidth={3} dot={{ fill: '#3B82F6', r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </div>

                            {/* Credibility & Compliance Row */}
                            <div className="grid grid-cols-2 gap-6 mb-8">
                                {/* Credibility Signals */}
                                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                    <div className="flex items-center justify-between mb-6">
                                        <h3 className="text-lg font-semibold flex items-center gap-2">
                                            <Shield className="w-5 h-5 text-purple-400" />
                                            Credibility Signals
                                        </h3>
                                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${result.achievability_assessment?.credibility_level === 'HIGH' ? 'bg-green-500/20 text-green-400' :
                                            result.achievability_assessment?.credibility_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
                                                'bg-red-500/20 text-red-400'
                                            }`}>
                                            {result.achievability_assessment?.credibility_level || 'MEDIUM'} Credibility
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        {Object.entries(result.achievability_assessment?.signals || {}).slice(0, 6).map(([key, value]) => (
                                            <div key={key} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                                                <span className="text-gray-300 capitalize">{key.replace(/_/g, ' ')}</span>
                                                {value?.detected ? (
                                                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                                                ) : (
                                                    <XCircle className="w-5 h-5 text-gray-600" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Regulatory Compliance */}
                                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl p-6">
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                        <Award className="w-5 h-5 text-amber-400" />
                                        Regulatory Compliance
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {Object.entries(result.regulatory_compliance?.summary || { eu_taxonomy: false, sbti: true, sllp: true }).map(([key, value]) => (
                                            <div key={key} className={`p-4 rounded-xl ${value ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-800/50 border border-gray-700'}`}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-sm font-medium text-gray-300 uppercase">{key.replace(/_/g, ' ')}</span>
                                                    {value ? (
                                                        <CheckCircle2 className="w-5 h-5 text-green-400" />
                                                    ) : (
                                                        <XCircle className="w-5 h-5 text-gray-500" />
                                                    )}
                                                </div>
                                                <p className={`text-xs ${value ? 'text-green-400' : 'text-gray-500'}`}>
                                                    {value ? 'Compliant' : 'Not Verified'}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Conditions & Risk Flags */}
                            {((result.final_decision?.conditions?.length || 0) > 0 || (result.risk_flags?.length || 0) > 0) && (
                                <div className="grid grid-cols-2 gap-6 mb-8">
                                    {/* Conditions */}
                                    {(result.final_decision?.conditions?.length || 0) > 0 && (
                                        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-amber-400">
                                                <AlertCircle className="w-5 h-5" />
                                                Conditions for Approval
                                            </h3>
                                            <div className="space-y-3">
                                                {(result.final_decision?.conditions || []).map((cond, i) => (
                                                    <div key={i} className="flex items-start gap-3 p-3 bg-gray-900/50 rounded-xl">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${cond.priority === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                                                            }`}>
                                                            {cond.priority}
                                                        </span>
                                                        <div>
                                                            <p className="font-medium text-white">{cond.condition}</p>
                                                            <p className="text-sm text-gray-400">{cond.detail}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Risk Flags */}
                                    {(result.risk_flags?.length || 0) > 0 && (
                                        <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-400">
                                                <AlertTriangle className="w-5 h-5" />
                                                Risk Flags
                                            </h3>
                                            <div className="space-y-3">
                                                {(result.risk_flags || []).map((flag, i) => (
                                                    <div key={i} className="p-3 bg-gray-900/50 rounded-xl">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className={`w-2 h-2 rounded-full ${flag.severity === 'HIGH' ? 'bg-red-400' : 'bg-amber-400'
                                                                }`} />
                                                            <p className="font-medium text-white">{flag.issue}</p>
                                                        </div>
                                                        <p className="text-sm text-gray-400 ml-4">{flag.recommendation}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                        </>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between pt-6 border-t border-gray-800">
                        <button
                            onClick={startNewAssessment}
                            className="px-6 py-3 text-gray-400 hover:text-white transition-colors"
                        >
                            Start New Assessment
                        </button>
                        <div className="flex gap-4">
                            <button className="flex items-center gap-2 px-6 py-3 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors">
                                <ExternalLink className="w-5 h-5" />
                                Share Report
                            </button>
                            <button
                                onClick={() => pdfMutation.mutate()}
                                disabled={pdfMutation.isPending}
                                className="flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-60 rounded-xl font-semibold transition-colors"
                            >
                                {pdfMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                                Download Full Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // Fallback
    return (
        <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
        </div>
    )
}
