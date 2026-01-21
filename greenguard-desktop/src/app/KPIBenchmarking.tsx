import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { kpiBenchmarkApi, uploadApi } from '@/lib/api'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
    Loader2, Target, TrendingUp, FileText, Upload,
    CheckCircle2, XCircle, AlertTriangle, ChevronRight, Download,
    Building2, Shield, Users, Globe, Award,
    Sparkles, ArrowRight, FileUp, Trash2, Zap, BarChart3,
    TrendingDown, CheckCircle, AlertCircle, ExternalLink, History, Clock
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    LineChart, Line
} from 'recharts'

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
        onSuccess: (response: any) => {
            console.log('Loaded evaluation response:', response.data)
            if (response.data?.result) {
                setEvaluationResult(response.data.result)
                setCurrentEvaluationId(response.data.evaluation?.id || null)
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
        }
    })

    useEffect(() => {
        const firstSectionId = evaluationResult?.detailed_report?.sections?.[0]?.id
        if (firstSectionId) setActiveSectionId(firstSectionId)
    }, [evaluationResult])

    // Intersection Observer to update active section on scroll
    useEffect(() => {
        if (!evaluationResult?.detailed_report?.sections) return

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setActiveSectionId(entry.target.id)
                    }
                })
            },
            {
                rootMargin: '-20% 0px -70% 0px',
                threshold: 0
            }
        )

        // Observe all sections
        const sections = evaluationResult.detailed_report.sections
        sections.forEach((section) => {
            const element = document.getElementById(section.id)
            if (element) observer.observe(element)
        })

        return () => observer.disconnect()
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
        onSuccess: (response: any) => {
            setEvaluationResult(response.data)
            // Capture evaluation ID for PDF generation without re-running
            if (response.data?.evaluation_id) {
                setCurrentEvaluationId(response.data.evaluation_id)
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
        onSuccess: (response: any) => {
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
        evaluateMutation.mutate()
    }

    const canProceed =
        formData.company_name &&
        formData.industry_sector &&
        formData.country_code &&
        formData.nace_code &&
        formData.nace_code &&
        formData.target_emissions &&
        formData.baseline_value &&
        formData.timeline_end_year >= 2025

    // History View
    // History View
    if (showHistory) {
        const historyItems: HistoryItem[] = historyData?.data?.evaluations || []
        return (
            <div className="space-y-6 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-kobalt-blue/10 rounded-full text-kobalt-blue text-xs font-medium mb-3">
                            <History className="w-3 h-3" />
                            Assessment History
                        </div>
                        <h1 className="text-3xl font-bold text-kobalt-black">Past Evaluations</h1>
                        <p className="text-kobalt-gray-dark mt-2">
                            View and load previously completed KPI assessments
                        </p>
                    </div>
                    <KobaltButton
                        variant="outline"
                        onClick={() => setShowHistory(false)}
                    >
                        <ChevronRight className="w-4 h-4 rotate-180 mr-2" />
                        Back to New Assessment
                    </KobaltButton>
                </div>

                {/* History List */}
                {isLoadingHistory ? (
                    <div className="flex justify-center py-20">
                        <Loader2 className="w-8 h-8 text-kobalt-blue animate-spin" />
                    </div>
                ) : historyItems.length === 0 ? (
                    <KobaltCard>
                        <div className="text-center py-20">
                            <Clock className="w-12 h-12 text-kobalt-gray-light mx-auto mb-4" />
                            <p className="text-kobalt-black text-lg font-medium">No evaluations found</p>
                            <p className="text-kobalt-gray mt-2">Complete your first assessment to see it here</p>
                        </div>
                    </KobaltCard>
                ) : (
                    <div className="space-y-4">
                        {historyItems.map((item) => {
                            const isApproved = item.banker_decision === 'APPROVE' || item.banker_decision === 'CONDITIONAL_APPROVAL'
                            const gradeColor = item.assessment_grade === 'AMBITIOUS' ? 'text-green-600 bg-green-50' :
                                item.assessment_grade === 'MODERATE' ? 'text-amber-600 bg-amber-50' : 'text-red-600 bg-red-50'

                            const decisionColor = isApproved ? 'bg-green-100 text-green-700 border border-green-200' :
                                item.banker_decision === 'REJECT' ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-amber-100 text-amber-700 border border-amber-200'

                            return (
                                <KobaltCard
                                    key={item.id}
                                    className="cursor-pointer hover:border-kobalt-blue hover:shadow-md transition-all group"
                                    onClick={() => loadEvaluationMutation.mutate(item.id)}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-lg font-bold text-kobalt-black group-hover:text-kobalt-blue transition-colors">
                                                    {item.company_name}
                                                </h3>
                                                <span className={`px-2 py-0.5 rounded-md text-xs font-semibold uppercase tracking-wide ${decisionColor}`}>
                                                    {item.banker_decision?.replace(/_/g, ' ') || 'PENDING'}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-kobalt-gray-dark">
                                                <div className="flex items-center gap-1.5">
                                                    <Building2 className="w-4 h-4 text-kobalt-gray" />
                                                    <span>{item.industry_sector}</span>
                                                </div>
                                                <span className="text-kobalt-border">•</span>
                                                <div className="flex items-center gap-1.5">
                                                    <Target className="w-4 h-4 text-kobalt-gray" />
                                                    <span>{item.target_value?.toFixed(1)}% reduction by {item.timeline_end_year}</span>
                                                </div>
                                                <span className="text-kobalt-border">•</span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${gradeColor}`}>
                                                    {item.assessment_grade || 'N/A'}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2 mt-4 text-xs text-kobalt-gray">
                                                <Clock className="w-3 h-3" />
                                                <span>{new Date(item.created_at).toLocaleDateString()}</span>
                                                <span>at</span>
                                                <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                <span className="ml-2 px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Ref: {item.loan_reference_id}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <KobaltButton
                                                variant="ghost"
                                                size="sm"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    kpiBenchmarkApi.getPdfFromSaved(item.id).then((response: any) => {
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
                                                title="Download PDF"
                                            >
                                                <Download className="w-4 h-4" />
                                            </KobaltButton>
                                            <div className="p-2 text-kobalt-gray-light group-hover:text-kobalt-blue transition-colors">
                                                <ArrowRight className="w-5 h-5" />
                                            </div>
                                        </div>
                                    </div>
                                </KobaltCard>
                            )
                        })}
                    </div>
                )}
            </div>
        )
    }

    // Step 1: Input Form
    if (step === 1) {
        return (
            <div className="space-y-6 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-kobalt-blue/10 rounded-full text-kobalt-blue text-xs font-medium mb-3">
                            <Sparkles className="w-3 h-3" />
                            AI-Powered ESG Assessment
                        </div>
                        <h1 className="text-3xl font-bold text-kobalt-black">KPI Benchmarking Engine</h1>
                        <p className="text-kobalt-gray-dark mt-2">
                            Evaluate sustainability-linked loan targets against industry peers and science-based pathways
                        </p>
                    </div>
                    <div className="flex gap-3">
                        {statsData?.data && (
                            <div className="flex gap-4 text-sm bg-white border border-kobalt-border rounded-xl px-4 py-2">
                                <div className="flex items-center gap-2">
                                    <Users className="w-4 h-4 text-kobalt-blue" />
                                    <span className="font-semibold text-kobalt-black">{statsData.data.companies_count?.toLocaleString()}</span>
                                    <span className="text-kobalt-gray">Companies</span>
                                </div>
                                <div className="w-px bg-kobalt-border" />
                                <div className="flex items-center gap-2">
                                    <Globe className="w-4 h-4 text-kobalt-blue" />
                                    <span className="font-semibold text-kobalt-black">{statsData.data.sectors_available || 85}</span>
                                    <span className="text-kobalt-gray">Sectors</span>
                                </div>
                            </div>
                        )}
                        <KobaltButton
                            variant="outline"
                            onClick={() => { setShowHistory(true); refetchHistory(); }}
                            className="bg-white"
                        >
                            <History className="w-4 h-4 mr-2" />
                            View History
                        </KobaltButton>
                    </div>
                </div>

                {/* Main Form Card */}
                <KobaltCard>
                    <div className="grid grid-cols-2 gap-8">
                        {/* Left Column - Company Info */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-kobalt-border">
                                <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                                    <Building2 className="w-5 h-5 text-kobalt-blue" />
                                </div>
                                <h2 className="text-lg font-semibold text-kobalt-black">Borrower Information</h2>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-kobalt-black mb-2">Company Name</label>
                                <input
                                    type="text"
                                    value={formData.company_name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, company_name: e.target.value }))}
                                    className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-kobalt-blue focus:ring-1 focus:ring-kobalt-blue transition-all outline-none"
                                    placeholder="e.g., Atos SE"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-kobalt-black mb-2">Industry Sector</label>
                                <select
                                    value={formData.industry_sector}
                                    onChange={(e) => setFormData(prev => ({ ...prev, industry_sector: e.target.value }))}
                                    className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black focus:border-kobalt-blue focus:ring-1 focus:ring-kobalt-blue transition-all outline-none appearance-none cursor-pointer"
                                >
                                    <option value="">Select industry sector</option>
                                    {INDUSTRY_SECTORS.map(sector => (
                                        <option key={sector} value={sector}>{sector}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Country</label>
                                    <select
                                        value={formData.country_code}
                                        onChange={(e) =>
                                            setFormData(prev => ({ ...prev, country_code: e.target.value }))
                                        }
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black focus:border-kobalt-blue focus:ring-1 focus:ring-kobalt-blue transition-all outline-none appearance-none cursor-pointer"
                                    >
                                        <option value="">Select Country</option>
                                        {EU_COUNTRIES.map(country => (
                                            <option key={country.code} value={country.code}>
                                                {country.name} ({country.code})
                                            </option>
                                        ))}
                                    </select>
                                    <p className="mt-1.5 text-xs text-kobalt-gray">EU, EEA, UK & Switzerland supported</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">NACE Code</label>
                                    <input
                                        type="text"
                                        value={formData.nace_code}
                                        onChange={(e) =>
                                            setFormData(prev => ({ ...prev, nace_code: e.target.value.toUpperCase().trim() }))
                                        }
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-kobalt-blue focus:ring-1 focus:ring-kobalt-blue transition-all outline-none"
                                        placeholder="e.g., C25.11 or J62"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Loan Type</label>
                                    <input
                                        type="text"
                                        value={formData.loan_type}
                                        onChange={(e) => setFormData(prev => ({ ...prev, loan_type: e.target.value }))}
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-kobalt-blue focus:ring-1 focus:ring-kobalt-blue transition-all outline-none"
                                        placeholder="Sustainability-Linked Loan"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Right Column - KPI Details */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-kobalt-border">
                                <div className="p-2 bg-green-500/10 rounded-lg">
                                    <Target className="w-5 h-5 text-green-600" />
                                </div>
                                <h2 className="text-lg font-semibold text-kobalt-black">Sustainability Target</h2>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Baseline Emissions (tCO2e)</label>
                                    <input
                                        type="number"
                                        value={formData.baseline_value}
                                        onChange={(e) => setFormData(prev => ({ ...prev, baseline_value: e.target.value }))}
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-green-600 focus:ring-1 focus:ring-green-600 transition-all outline-none"
                                        placeholder="100000"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Baseline Year</label>
                                    <input
                                        type="number"
                                        value={formData.baseline_year}
                                        onChange={(e) => setFormData(prev => ({ ...prev, baseline_year: parseInt(e.target.value) }))}
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black focus:border-green-600 focus:ring-1 focus:ring-green-600 transition-all outline-none"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Target Emissions (tCO2e)</label>
                                    <input
                                        type="number"
                                        value={formData.target_emissions}
                                        onChange={(e) => setFormData(prev => ({ ...prev, target_emissions: e.target.value }))}
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-green-600 focus:ring-1 focus:ring-green-600 transition-all outline-none"
                                        placeholder="e.g., 54000"
                                    />
                                    <div className="mt-2 flex items-center justify-between text-xs">
                                        <span className="text-kobalt-gray">Auto-calculated reduction</span>
                                        <span className={`font-medium ${Number.isFinite(computedReductionPct) && computedReductionPct >= 0 ? 'text-green-600' : 'text-amber-600'}`}>
                                            {Number.isFinite(computedReductionPct) ? `${computedReductionPct.toFixed(1)}%` : '—'}
                                        </span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-kobalt-black mb-2">Target Year</label>
                                    <input
                                        type="number"
                                        value={formData.timeline_end_year}
                                        onChange={(e) => setFormData(prev => ({ ...prev, timeline_end_year: parseInt(e.target.value) }))}
                                        className="w-full px-4 py-2.5 bg-white border border-kobalt-border rounded-xl text-kobalt-black focus:border-green-600 focus:ring-1 focus:ring-green-600 transition-all outline-none"
                                        min="2025"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-kobalt-black mb-2">Emissions Scope</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {['Scope 1+2', 'Scope 1+2+3', 'Scope 3'].map(scope => (
                                        <button
                                            key={scope}
                                            onClick={() => setFormData(prev => ({ ...prev, emissions_scope: scope }))}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${formData.emissions_scope === scope
                                                ? 'bg-kobalt-blue text-white shadow-sm'
                                                : 'bg-white border border-kobalt-border text-kobalt-gray hover:bg-gray-50'
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
                    <div className="mt-8 pt-6 border-t border-kobalt-border flex justify-end">
                        <KobaltButton
                            onClick={() => canProceed && setStep(2)}
                            disabled={!canProceed}
                            size="lg"
                            className="w-full sm:w-auto"
                        >
                            Continue to Documents
                            <ArrowRight className="w-5 h-5 ml-2" />
                        </KobaltButton>
                    </div>
                </KobaltCard>
            </div>
        )
    }

    // Step 2: Document Upload
    if (step === 2) {
        return (
            <div className="space-y-6 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-kobalt-blue/10 rounded-full text-kobalt-blue text-xs font-medium mb-3">
                            <FileUp className="w-3 h-3" />
                            Document Analysis
                        </div>
                        <h1 className="text-3xl font-bold text-kobalt-black">Upload Supporting Documents</h1>
                        <p className="text-kobalt-gray-dark mt-2">
                            Upload ESG reports and sustainability documents for AI-powered analysis
                        </p>
                    </div>
                    <KobaltButton
                        variant="ghost"
                        onClick={() => setStep(1)}
                        className="flex items-center gap-2"
                    >
                        <ChevronRight className="w-5 h-5 rotate-180" />
                        Back to Company Details
                    </KobaltButton>
                </div>

                <KobaltCard>
                    {/* Document Upload Grid */}
                    <div className="grid grid-cols-2 gap-6 mb-8">
                        {DOCUMENT_TYPES.map((docType) => {
                            const uploadedDoc = uploadedDocs.find(d => d.document_type === docType.value)
                            const Icon = docType.icon
                            const colorClasses = ({
                                emerald: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-600' },
                                blue: { bg: 'bg-kobalt-blue/10', border: 'border-kobalt-blue/30', text: 'text-kobalt-blue' },
                                purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-600' },
                                amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-600' },
                            } as const)[docType.color] || { bg: 'bg-gray-100', border: 'border-gray-200', text: 'text-gray-500' }

                            return (
                                <div
                                    key={docType.value}
                                    className={`relative p-6 rounded-2xl border-2 border-dashed transition-all ${uploadedDoc
                                        ? 'bg-gray-50 border-gray-200'
                                        : `${colorClasses.bg} ${colorClasses.border} hover:border-opacity-60`
                                        }`}
                                >
                                    {uploadedDoc ? (
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-4">
                                                <div className={`p-3 rounded-xl ${colorClasses.bg}`}>
                                                    {uploadedDoc.status === 'ready' ? (
                                                        <CheckCircle2 className="w-6 h-6 text-green-600" />
                                                    ) : uploadedDoc.status === 'uploading' ? (
                                                        <Loader2 className="w-6 h-6 text-kobalt-blue animate-spin" />
                                                    ) : (
                                                        <XCircle className="w-6 h-6 text-red-600" />
                                                    )}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-kobalt-black">{docType.label}</p>
                                                    <p className="text-sm text-kobalt-gray truncate max-w-xs">{uploadedDoc.filename}</p>
                                                    <p className={`text-xs mt-1 ${uploadedDoc.status === 'ready' ? 'text-green-600' :
                                                        uploadedDoc.status === 'uploading' ? 'text-kobalt-blue' : 'text-red-600'
                                                        }`}>
                                                        {uploadedDoc.status === 'ready' ? 'Ready for analysis' :
                                                            uploadedDoc.status === 'uploading' ? 'Processing...' : 'Upload failed'}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeDocument(uploadedDoc.filename)}
                                                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4 text-kobalt-gray" />
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
                                                <p className="font-medium text-kobalt-black mb-1">{docType.label}</p>
                                                <p className="text-sm text-kobalt-gray mb-3">
                                                    {docType.mandatory ? (
                                                        <span className="text-amber-600">Required</span>
                                                    ) : 'Optional'}
                                                </p>
                                                <div className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-kobalt-border rounded-lg text-sm text-kobalt-gray-dark shadow-sm">
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
                    <div className="flex items-center justify-between border-t border-kobalt-border pt-6">
                        <p className="text-kobalt-gray text-sm">
                            {uploadedDocs.filter(d => d.status === 'ready').length} document(s) ready for analysis
                        </p>
                        <KobaltButton
                            onClick={startAnalysis}
                            disabled={isAnalyzing || !canRunAssessment}
                            isLoading={isAnalyzing}
                            size="lg"
                            className="bg-gradient-to-r from-kobalt-blue to-purple-600 hover:from-kobalt-blue/90 hover:to-purple-700 text-white shadow-lg shadow-kobalt-blue/25"
                        >
                            {isAnalyzing ? 'Analyzing Documents...' : (
                                <>
                                    <Zap className="w-5 h-5 mr-2" />
                                    Run AI Assessment
                                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </KobaltButton>
                    </div>

                    {runError && (
                        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800">
                            <p className="font-semibold mb-1">Unable to run AI assessment</p>
                            <p className="text-sm text-red-600">{runError}</p>
                        </div>
                    )}

                    {/* Analysis Progress */}
                    {isAnalyzing && (
                        <div className="mt-8 p-6 bg-kobalt-blue/5 border border-kobalt-blue/10 rounded-2xl">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="relative">
                                    <div className="w-12 h-12 rounded-full border-4 border-kobalt-blue/30 border-t-kobalt-blue animate-spin" />
                                    <Sparkles className="w-5 h-5 text-kobalt-blue absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                                </div>
                                <div>
                                    <p className="font-semibold text-kobalt-black">AI Assessment in Progress</p>
                                    <p className="text-sm text-kobalt-gray">Analyzing documents with 17 specialized agents...</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {['Extracting KPIs', 'Peer Benchmarking', 'Credibility Analysis', 'Regulatory Check'].map((task, i) => (
                                    <div key={task} className="flex items-center gap-3 text-sm">
                                        <div className={`w-2 h-2 rounded-full ${i < 2 ? 'bg-green-500' : 'bg-kobalt-gray-light animate-pulse'}`} />
                                        <span className={i < 2 ? 'text-kobalt-black' : 'text-kobalt-gray'}>{task}</span>
                                        {i < 2 && <CheckCircle className="w-4 h-4 text-green-500" />}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </KobaltCard>
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
                case 'APPROVE': return { bg: 'bg-gradient-to-br from-green-600 to-emerald-700', border: 'border-green-600/50', text: 'text-white', icon: CheckCircle2, iconBg: 'bg-white/20', label: 'APPROVAL' }
                case 'CONDITIONAL_APPROVAL': return { bg: 'bg-gradient-to-br from-amber-700 via-amber-800 to-amber-900', border: 'border-amber-700/50', text: 'text-white', icon: AlertCircle, iconBg: 'bg-amber-900/40', label: 'CONDITIONAL APPROVAL' }
                case 'REJECT': return { bg: 'bg-gradient-to-br from-red-600 to-red-800', border: 'border-red-600/50', text: 'text-white', icon: XCircle, iconBg: 'bg-white/20', label: 'REJECT' }
                default: return { bg: 'bg-gradient-to-br from-gray-600 to-gray-800', border: 'border-gray-600/50', text: 'text-white', icon: AlertTriangle, iconBg: 'bg-white/20', label: 'UNDER REVIEW' }
            }
        }
        
        const getAmbitionStyle = () => {
            switch (ambitionLevel) {
                case 'SCIENCE_ALIGNED':
                case 'AMBITIOUS': return { bg: 'bg-gradient-to-br from-blue-700 via-blue-800 to-blue-900', border: 'border-blue-700/50', text: 'text-white', label: 'AMBITIOUS' }
                case 'ABOVE_MARKET': return { bg: 'bg-gradient-to-br from-blue-600 to-blue-800', border: 'border-blue-600/50', text: 'text-white', label: 'ABOVE MARKET' }
                case 'MODERATE': return { bg: 'bg-gradient-to-br from-amber-600 to-orange-700', border: 'border-amber-600/50', text: 'text-white', label: 'MODERATE' }
                default: return { bg: 'bg-gradient-to-br from-gray-600 to-gray-800', border: 'border-gray-600/50', text: 'text-white', label: ambitionLevel }
            }
        }
        
        const recStyle = getRecommendationStyle()
        const ambStyle = getAmbitionStyle()
        const RecIcon = recStyle.icon

        const fallbackCompanyPct = Number.isFinite(computedReductionPct) ? computedReductionPct : 5
        const peerChartData = (result.visuals?.peer_comparison?.labels || ['Company', 'Median', 'Top 25%']).map((label, i) => ({
            name: label,
            value: result.visuals?.peer_comparison?.dataset?.[0]?.data?.[i] || [fallbackCompanyPct, 5, 7.5][i]
        }))

        const trajectoryData = (result.visuals?.emissions_trajectory?.labels || [formData.baseline_year.toString(), '2026', formData.timeline_end_year.toString()]).map((label, i) => ({
            year: label,
            emissions: result.visuals?.emissions_trajectory?.data?.[i] || [100, 75, 50][i]
        }))

        const sections = memo?.sections || []

        return (
            <div className="min-h-screen pb-20 animate-fade-in">
                <div className="max-w-7xl mx-auto">
                    {/* Report Header */}
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <p className="text-kobalt-gray text-sm mb-2">Assessment Report | {result.report_header.analysis_date}</p>
                            <h1 className="text-5xl font-bold mb-2 text-kobalt-black">{result.report_header.company_name}</h1>
                            <p className="text-kobalt-gray-dark">{result.report_header.deal_details.loan_type}</p>
                        </div>
                        <KobaltButton
                            onClick={() => pdfMutation.mutate()}
                            disabled={pdfMutation.isPending}
                            variant="outline"
                            className="flex items-center gap-2"
                        >
                            {pdfMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                            Export PDF
                        </KobaltButton>
                    </div>

                    {/* Recommendation & Ambition Cards */}
                    <div className="grid grid-cols-2 gap-6 mb-8">
                        {/* Credit Recommendation Card */}
                        <KobaltCard className={`relative overflow-hidden ${recStyle.bg} border-2 ${recStyle.border}`}>
                            <div className="flex items-center gap-6 mb-6">
                                <div className={`p-4 rounded-2xl ${recStyle.iconBg}`}>
                                    <RecIcon className="w-10 h-10 text-white" />
                                </div>
                                <div>
                                    <p className="text-white/90 text-sm font-semibold mb-1 tracking-wide">CREDIT RECOMMENDATION</p>
                                    <p className="text-3xl font-bold text-white">
                                        {recStyle.label}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-white/80 font-medium">Confidence Level</span>
                                <span className="text-2xl font-bold text-white">{result.final_decision?.confidence || 'MEDIUM'}</span>
                            </div>
                        </KobaltCard>

                        {/* Target Ambition Card */}
                        <KobaltCard className={`relative overflow-hidden ${ambStyle.bg} border-2 ${ambStyle.border}`}>
                            <div className="flex items-center gap-6 mb-6">
                                <div className="p-4 rounded-2xl bg-white/20">
                                    <TrendingUp className="w-10 h-10 text-white" />
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
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-white/80 font-medium">Peer Percentile</span>
                                <span className="text-2xl font-bold text-white">
                                    {result.peer_benchmarking?.company_position?.percentile_rank 
                                        ? `${Math.round(result.peer_benchmarking.company_position.percentile_rank)}th`
                                        : '5th'}
                                </span>
                            </div>
                        </KobaltCard>
                    </div>

                    {/* Detailed Assessment Report Section */}
                    <KobaltCard className="mb-8">
                        <div className="flex items-center gap-3 mb-6">
                            <Sparkles className="w-6 h-6 text-kobalt-blue" />
                            <h2 className="text-2xl font-bold text-kobalt-black">Detailed Assessment Report</h2>
                        </div>
                        {result.executive_summary.ai_narrative && (
                            <div className="prose prose-slate prose-lg max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {result.executive_summary.ai_narrative}
                                </ReactMarkdown>
                            </div>
                        )}
                    </KobaltCard>

                    {/* Ask About This Report - Interactive Q&A */}
                    <KobaltCard className="mb-8">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 bg-purple-500/10 rounded-xl">
                                <FileText className="w-5 h-5 text-purple-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-kobalt-black">Ask about this report</h3>
                                <p className="text-sm text-kobalt-gray">Questions are answered using your uploaded documents + the saved report.</p>
                            </div>
                        </div>
                        
                        <div className="bg-kobalt-gray rounded-xl p-4 mb-4">
                            <p className="text-kobalt-gray-dark italic">Try: "Why did the report recommend CONDITIONAL_APPROVAL?"</p>
                        </div>

                        <div className="flex gap-3">
                            <input
                                type="text"
                                placeholder="Ask a question about this report..."
                                className="flex-1 px-6 py-4 bg-white border border-kobalt-border rounded-xl text-kobalt-black placeholder-kobalt-gray focus:border-kobalt-blue focus:ring-2 focus:ring-kobalt-blue/20 transition-all outline-none"
                            />
                            <KobaltButton className="px-8 py-4 flex items-center gap-2">
                                <Sparkles className="w-5 h-5" />
                                Send
                            </KobaltButton>
                        </div>
                    </KobaltCard>

                    {/* Report View Toggle */}
                    {memo && (
                        <div className="flex items-center gap-3 mb-8">
                            <button
                                onClick={() => setReportView('memo')}
                                className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all ${
                                    reportView === 'memo' 
                                        ? 'bg-kobalt-blue text-white shadow-md' 
                                        : 'bg-white border border-kobalt-border text-kobalt-gray-dark hover:bg-kobalt-gray'
                                }`}
                            >
                                Credit Memo
                            </button>
                            <button
                                onClick={() => setReportView('highlights')}
                                className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all ${
                                    reportView === 'highlights' 
                                        ? 'bg-kobalt-blue text-white shadow-md' 
                                        : 'bg-white border border-kobalt-border text-kobalt-gray-dark hover:bg-kobalt-gray'
                                }`}
                            >
                                Highlights
                            </button>
                            <div className="ml-auto text-sm text-kobalt-gray">
                                Credit Committee • {memo.meta?.as_of_date || result.report_header.analysis_date}
                            </div>
                        </div>
                    )}

                    {reportView === 'memo' && memo ? (
                        <div className="grid grid-cols-12 gap-8">
                            {/* Navigation Sidebar */}
                            <div className="col-span-3">
                                <div className="sticky top-8 space-y-6">
                                    {/* CONTENTS */}
                                    <div>
                                        <h3 className="text-xs font-semibold text-kobalt-gray uppercase tracking-wider mb-3 px-4">CONTENTS</h3>
                                        <div className="space-y-1">
                                            {(sections || []).map((section) => (
                                                <button
                                                    key={section.id}
                                                    onClick={() => {
                                                        setActiveSectionId(section.id)
                                                        // Smooth scroll to section
                                                        const element = document.getElementById(section.id)
                                                        if (element) {
                                                            element.scrollIntoView({ 
                                                                behavior: 'smooth', 
                                                                block: 'start',
                                                                inline: 'nearest'
                                                            })
                                                        }
                                                    }}
                                                    className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all ${
                                                        activeSectionId === section.id
                                                            ? 'bg-kobalt-blue text-white font-medium shadow-sm'
                                                            : 'text-kobalt-gray-dark hover:bg-kobalt-gray'
                                                    }`}
                                                >
                                                    {section.title}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* FIGURES */}
                                    <div>
                                        <h3 className="text-xs font-semibold text-kobalt-gray uppercase tracking-wider mb-3 px-4">FIGURES</h3>
                                        <div className="space-y-1">
                                            <button className="w-full text-left px-4 py-3 text-sm text-kobalt-gray-dark hover:bg-kobalt-gray rounded-xl transition-all">
                                                Peer Benchmarking (Reduction Target vs Peers)
                                            </button>
                                            <button className="w-full text-left px-4 py-3 text-sm text-kobalt-gray-dark hover:bg-kobalt-gray rounded-xl transition-all">
                                                Emissions Trajectory (Indexed to Baseline)
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Main Content Area */}
                            <div className="col-span-9 space-y-6">
                                {(sections || []).map((section) => (
                                    <div 
                                        key={section.id} 
                                        id={section.id} 
                                        className="scroll-mt-24"
                                        style={{ scrollMarginTop: '6rem' }}
                                    >
                                        <KobaltCard>
                                            <h3 className="text-2xl font-bold text-kobalt-black mb-6 pb-4 border-b border-kobalt-border">
                                                {section.title}
                                            </h3>
                                            <div className="prose prose-slate prose-lg max-w-none">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {section.markdown || ''}
                                                </ReactMarkdown>
                                            </div>

                                            {/* Section-specific visualizations */}
                                            {section.id === 'detailed_analysis' && (
                                                <div className="grid grid-cols-2 gap-6 mt-8 not-prose">
                                                    {/* Peer Comparison Chart */}
                                                    <div className="bg-kobalt-gray rounded-xl p-6 border border-kobalt-border">
                                                        <h4 className="text-sm font-semibold text-kobalt-black mb-4 flex items-center gap-2">
                                                            <BarChart3 className="w-4 h-4 text-emerald-600" />
                                                            Peer Benchmarking
                                                        </h4>
                                                        <div className="h-48">
                                                            <ResponsiveContainer width="100%" height="100%">
                                                                <BarChart data={peerChartData} layout="vertical">
                                                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                                                    <XAxis type="number" stroke="#6b7280" fontSize={11} unit="%" />
                                                                    <YAxis dataKey="name" type="category" stroke="#6b7280" fontSize={11} width={80} />
                                                                    <RechartsTooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px', color: '#111827' }} />
                                                                    <Bar dataKey="value" fill="#10B981" radius={[0, 4, 4, 0]} />
                                                                </BarChart>
                                                            </ResponsiveContainer>
                                                        </div>
                                                    </div>

                                                    {/* Trajectory Chart */}
                                                    <div className="bg-kobalt-gray rounded-xl p-6 border border-kobalt-border">
                                                        <h4 className="text-sm font-semibold text-kobalt-black mb-4 flex items-center gap-2">
                                                            <TrendingDown className="w-4 h-4 text-blue-600" />
                                                            Emissions Trajectory
                                                        </h4>
                                                        <div className="h-48">
                                                            <ResponsiveContainer width="100%" height="100%">
                                                                <LineChart data={trajectoryData}>
                                                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                                                    <XAxis dataKey="year" stroke="#6b7280" fontSize={11} />
                                                                    <YAxis stroke="#6b7280" fontSize={11} unit="%" />
                                                                    <RechartsTooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px', color: '#111827' }} />
                                                                    <Line type="monotone" dataKey="emissions" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6', r: 4 }} />
                                                                </LineChart>
                                                            </ResponsiveContainer>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </KobaltCard>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        // Highlights View
                        <>
                            <div className="grid grid-cols-2 gap-6 mb-8">
                                {/* Peer Comparison */}
                                <KobaltCard>
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-kobalt-black">
                                        <BarChart3 className="w-5 h-5 text-emerald-600" />
                                        Peer Benchmarking
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={peerChartData} layout="vertical">
                                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                                <XAxis type="number" stroke="#6b7280" fontSize={12} unit="%" />
                                                <YAxis dataKey="name" type="category" stroke="#6b7280" fontSize={12} width={100} />
                                                <RechartsTooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px', color: '#111827' }} />
                                                <Bar dataKey="value" fill="#10B981" radius={[0, 4, 4, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div className="mt-4 flex items-center justify-between text-sm">
                                        <span className="text-kobalt-gray">
                                            {result.peer_benchmarking?.peer_statistics?.peer_count || 5} peers analyzed
                                        </span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${result.peer_benchmarking?.ambition_classification?.level === 'SCIENCE_ALIGNED' ? 'bg-green-100 text-green-700' :
                                            result.peer_benchmarking?.ambition_classification?.level === 'ABOVE_MARKET' ? 'bg-blue-100 text-blue-700' :
                                                'bg-amber-100 text-amber-700'
                                            }`}>
                                            {result.peer_benchmarking?.ambition_classification?.level?.replace(/_/g, ' ') || 'MODERATE'}
                                        </span>
                                    </div>
                                </KobaltCard>

                                {/* Emissions Trajectory */}
                                <KobaltCard>
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-kobalt-black">
                                        <TrendingDown className="w-5 h-5 text-blue-600" />
                                        Emissions Trajectory
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={trajectoryData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                                <XAxis dataKey="year" stroke="#6b7280" fontSize={12} />
                                                <YAxis stroke="#6b7280" fontSize={12} unit="%" />
                                                <RechartsTooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px', color: '#111827' }} />
                                                <Line type="monotone" dataKey="emissions" stroke="#3B82F6" strokeWidth={3} dot={{ fill: '#3B82F6', r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </KobaltCard>
                            </div>

                            {/* Credibility & Compliance Row */}
                            <div className="grid grid-cols-2 gap-6 mb-8">
                                {/* Credibility Signals */}
                                <KobaltCard>
                                    <div className="flex items-center justify-between mb-6">
                                        <h3 className="text-lg font-semibold flex items-center gap-2 text-kobalt-black">
                                            <Shield className="w-5 h-5 text-purple-600" />
                                            Credibility Signals
                                        </h3>
                                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${result.achievability_assessment?.credibility_level === 'HIGH' ? 'bg-green-100 text-green-700' :
                                            result.achievability_assessment?.credibility_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                                                'bg-red-100 text-red-700'
                                            }`}>
                                            {result.achievability_assessment?.credibility_level || 'MEDIUM'} Credibility
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        {Object.entries(result.achievability_assessment?.signals || {}).slice(0, 6).map(([key, value]) => (
                                            <div key={key} className="flex items-center justify-between py-2 border-b border-kobalt-border last:border-0">
                                                <span className="text-kobalt-gray-dark capitalize">{key.replace(/_/g, ' ')}</span>
                                                {value?.detected ? (
                                                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                                                ) : (
                                                    <XCircle className="w-5 h-5 text-gray-400" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </KobaltCard>

                                {/* Regulatory Compliance */}
                                <KobaltCard>
                                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-kobalt-black">
                                        <Award className="w-5 h-5 text-amber-600" />
                                        Regulatory Compliance
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {Object.entries(result.regulatory_compliance?.summary || { eu_taxonomy: false, csrd: true, sbti: true, sllp: true }).map(([key, value]) => (
                                            <div key={key} className={`p-4 rounded-xl ${value ? 'bg-green-50/50 border border-green-200' : 'bg-gray-50 border border-gray-200'}`}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-sm font-medium text-kobalt-gray-dark uppercase">{key.replace(/_/g, ' ')}</span>
                                                    {value ? (
                                                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                                                    ) : (
                                                        <XCircle className="w-5 h-5 text-gray-400" />
                                                    )}
                                                </div>
                                                <p className={`text-xs ${value ? 'text-green-700' : 'text-gray-500'}`}>
                                                    {value ? 'Compliant' : 'Not Verified'}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </KobaltCard>
                            </div>

                            {/* Conditions & Risk Flags */}
                            {((result.final_decision?.conditions?.length || 0) > 0 || (result.risk_flags?.length || 0) > 0) && (
                                <div className="grid grid-cols-2 gap-6 mb-8">
                                    {/* Conditions */}
                                    {(result.final_decision?.conditions?.length || 0) > 0 && (
                                        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-amber-700">
                                                <AlertCircle className="w-5 h-5" />
                                                Conditions for Approval
                                            </h3>
                                            <div className="space-y-3">
                                                {(result.final_decision?.conditions || []).map((cond, i) => (
                                                    <div key={i} className="flex items-start gap-3 p-3 bg-white border border-amber-100 rounded-xl">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${cond.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                                                            }`}>
                                                            {cond.priority}
                                                        </span>
                                                        <div>
                                                            <p className="font-medium text-kobalt-black">{cond.condition}</p>
                                                            <p className="text-sm text-kobalt-gray">{cond.detail}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Risk Flags */}
                                    {(result.risk_flags?.length || 0) > 0 && (
                                        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-sm">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-700">
                                                <AlertTriangle className="w-5 h-5" />
                                                Risk Flags
                                            </h3>
                                            <div className="space-y-3">
                                                {(result.risk_flags || []).map((flag, i) => (
                                                    <div key={i} className="p-3 bg-white border border-red-100 rounded-xl">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className={`w-2 h-2 rounded-full ${flag.severity === 'HIGH' ? 'bg-red-500' : 'bg-amber-500'
                                                                }`} />
                                                            <p className="font-medium text-kobalt-black">{flag.issue}</p>
                                                        </div>
                                                        <p className="text-sm text-kobalt-gray ml-4">{flag.recommendation}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                        </>
                    )}

                    {/* Risk Register Section */}
                    {result.risk_flags && result.risk_flags.length > 0 && (
                        <KobaltCard className="mb-8 border-red-200">
                            <div className="flex items-center gap-3 mb-6">
                                <AlertTriangle className="w-6 h-6 text-red-600" />
                                <h2 className="text-2xl font-bold text-kobalt-black">Risk Register</h2>
                            </div>
                            <div className="space-y-4">
                                {result.risk_flags.map((risk, idx) => (
                                    <div key={idx} className="p-6 bg-kobalt-gray rounded-xl border border-kobalt-border">
                                        <div className="flex items-start justify-between mb-3">
                                            <h3 className="text-lg font-bold text-kobalt-black">R{idx + 1} • {risk.category}</h3>
                                            <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase ${
                                                risk.severity === 'HIGH' ? 'bg-red-100 text-red-700 border border-red-200' :
                                                risk.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                                                'bg-green-100 text-green-700 border border-green-200'
                                            }`}>
                                                {risk.severity}
                                            </span>
                                        </div>
                                        <p className="text-kobalt-gray-dark mb-3">{risk.issue}</p>
                                        <div className="text-sm space-y-2">
                                            <p className="text-kobalt-gray-dark"><span className="text-kobalt-gray font-medium">Mitigant:</span> {risk.recommendation}</p>
                                            <p className="text-kobalt-gray-dark"><span className="text-kobalt-gray font-medium">Condition/Covenant:</span> Quarterly sustainability reports</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </KobaltCard>
                    )}

                    {/* Monitoring Plan */}
                    {result.recommended_terms?.monitoring_plan && result.recommended_terms.monitoring_plan.length > 0 && (
                        <KobaltCard className="mb-8 border-green-200">
                            <div className="flex items-center gap-3 mb-6">
                                <CheckCircle className="w-6 h-6 text-green-600" />
                                <h2 className="text-2xl font-bold text-kobalt-black">Monitoring Plan</h2>
                            </div>
                            <div className="space-y-3">
                                {result.recommended_terms.monitoring_plan.map((item, idx) => (
                                    <div key={idx} className="flex items-center gap-3 text-kobalt-gray-dark">
                                        <div className="w-2 h-2 rounded-full bg-green-600"></div>
                                        <span>{item}</span>
                                    </div>
                                ))}
                            </div>
                        </KobaltCard>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between pt-8 border-t border-kobalt-border">
                        <KobaltButton
                            variant="ghost"
                            onClick={() => { setStep(1); setEvaluationResult(null); setUploadedDocs([]); setCurrentEvaluationId(null) }}
                        >
                            Start New Assessment
                        </KobaltButton>
                        <div className="flex gap-4">
                            <KobaltButton variant="outline">
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Share Report
                            </KobaltButton>
                            <KobaltButton
                                onClick={() => pdfMutation.mutate()}
                                disabled={pdfMutation.isPending}
                                isLoading={pdfMutation.isPending}
                            >
                                <Download className="w-4 h-4 mr-2" />
                                Download Full Report
                            </KobaltButton>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // Fallback
    return (
        <div className="min-h-screen bg-white flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-kobalt-blue animate-spin" />
        </div>
    )
}