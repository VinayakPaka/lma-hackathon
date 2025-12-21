import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { kpiBenchmarkApi, uploadApi } from '@/lib/api'
import {
    BarChart3, Loader2, Target, TrendingUp, FileText, Upload,
    CheckCircle2, XCircle, AlertTriangle, ChevronRight, Download,
    Building2, Scale, FileCheck,
    Shield, AlertCircle, Info, Users, Globe, Award
} from 'lucide-react'

// Types based on backend response
interface EvaluationResult {
    report_header: {
        company_name: string
        deal_details: {
            loan_type: string
            facility_amount: string
            tenor_years: number
        }
        analysis_date: string
    }
    executive_summary: {
        overall_recommendation: string
        recommendation_rationale: string
        key_findings: Array<{
            category: string
            assessment: string
            detail: string
        }>
        conditions_for_approval: string[]
    }
    peer_benchmarking: {
        peer_statistics: {
            peer_count: number
            confidence_level: string
            percentiles: {
                median: number
                p75: number
            }
        }
        company_position: {
            percentile_rank: number
            classification: string
        }
        ambition_classification: {
            level: string
            rationale: string
        }
        recommendation: {
            action: string
            suggested_minimum?: number
            message?: string
        }
    }
    achievability_assessment: {
        credibility_level: string
        signals: Record<string, {
            detected: boolean
            evidence?: string
        }>
        gaps: Array<{
            signal: string
            recommendation: string
        }>
    }
    risk_flags: Array<{
        severity: string
        category: string
        issue: string
        recommendation: string
    }>
    regulatory_compliance: {
        summary: Record<string, boolean>
    }
    final_decision: {
        recommendation: string
        confidence: string
        conditions: Array<{
            condition: string
            detail: string
            priority: string
        }>
    }
}

interface UploadedDocument {
    id: number
    filename: string
    document_type: string
    is_primary: boolean
}

const EMISSION_SCOPES = [
    { value: 'Scope 1+2', label: 'Scope 1+2 (Direct + Purchased Energy)' },
    { value: 'Scope 1', label: 'Scope 1 (Direct Emissions)' },
    { value: 'Scope 2', label: 'Scope 2 (Purchased Energy)' },
    { value: 'Scope 3', label: 'Scope 3 (Value Chain)' },
]

const DOCUMENT_TYPES = [
    { value: 'csrd_report', label: 'CSRD Report', mandatory: true, description: 'Non-Financial Reporting Statement' },
    { value: 'spts', label: 'SPTs Document', mandatory: true, description: 'Sustainability Performance Targets' },
    { value: 'spo', label: 'Second Party Opinion', mandatory: false, description: 'Independent target review' },
    { value: 'taxonomy_report', label: 'EU Taxonomy Report', mandatory: false, description: 'Green alignment %' },
    { value: 'transition_plan', label: 'Transition Plan', mandatory: false, description: 'Decarbonization roadmap' },
]

export default function KPIBenchmarking() {
    const [step, setStep] = useState(1)
    const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
    const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null)
    const [evaluationError, setEvaluationError] = useState<string | null>(null)
    const [pendingDocType, setPendingDocType] = useState<string>('csrd_report')
    const [formData, setFormData] = useState({
        company_name: '',
        industry_sector: '',
        metric: 'GHG Emissions Reduction',
        target_value: '',
        target_unit: 'tCO2e',
        baseline_value: '',
        baseline_year: new Date().getFullYear() - 1,
        timeline_end_year: 2030,
        emissions_scope: 'Scope 1+2',
        ticker: '',
        facility_amount: '',
        tenor_years: 5,
        margin_adjustment_bps: 15,
        loan_type: 'Sustainability-Linked Loan',
    })

    // Get available sectors
    const { data: sectorsData } = useQuery({
        queryKey: ['sbti-sectors'],
        queryFn: () => kpiBenchmarkApi.getSectors(),
    })

    // Get SBTi stats
    const { data: statsData } = useQuery({
        queryKey: ['sbti-stats'],
        queryFn: () => kpiBenchmarkApi.getStats(),
    })

    // Upload document mutation
    const uploadMutation = useMutation({
        mutationFn: (file: File) => uploadApi.uploadDocument(file),
        onSuccess: (response, file) => {
            const newDoc: UploadedDocument = {
                id: response.data.document_id,
                filename: file.name,
                document_type: pendingDocType,
                is_primary: uploadedDocs.length === 0,
            }
            setUploadedDocs(prev => [...prev, newDoc])
        },
        onError: (error: Error) => {
            console.error('Upload failed:', error)
            setEvaluationError(`Document upload failed: ${error.message}`)
        },
    })

    // Evaluation mutation
    const evaluateMutation = useMutation({
        mutationFn: () => {
            setEvaluationError(null)
            // Build documents array only if we have uploaded docs with valid IDs
            const documents = uploadedDocs
                .filter(d => d.id && d.id > 0)
                .map(d => ({
                    document_id: d.id,
                    document_type: d.document_type,
                    is_primary: d.is_primary,
                }))

            return kpiBenchmarkApi.evaluate({
                company_name: formData.company_name,
                industry_sector: formData.industry_sector,
                metric: formData.metric,
                target_value: parseFloat(formData.target_value),
                target_unit: formData.target_unit,
                baseline_value: parseFloat(formData.baseline_value),
                baseline_year: formData.baseline_year,
                timeline_end_year: formData.timeline_end_year,
                emissions_scope: formData.emissions_scope,
                ticker: formData.ticker || undefined,
                facility_amount: formData.facility_amount || undefined,
                tenor_years: formData.tenor_years,
                margin_adjustment_bps: formData.margin_adjustment_bps,
                loan_type: formData.loan_type,
                documents: documents.length > 0 ? documents : undefined,
            })
        },
        onSuccess: (response) => {
            setEvaluationError(null)
            setEvaluationResult(response.data)
            setStep(4)
        },
        onError: (error: Error) => {
            console.error('Evaluation failed:', error)
            setEvaluationError(`Evaluation failed: ${error.message}. Please check your inputs and try again.`)
        },
    })

    // Download PDF mutation
    const downloadPdfMutation = useMutation({
        mutationFn: () => {
            // Build documents array only if we have uploaded docs with valid IDs
            const documents = uploadedDocs
                .filter(d => d.id && d.id > 0)
                .map(d => ({
                    document_id: d.id,
                    document_type: d.document_type,
                    is_primary: d.is_primary,
                }))

            return kpiBenchmarkApi.evaluatePdf({
                company_name: formData.company_name,
                industry_sector: formData.industry_sector,
                metric: formData.metric,
                target_value: parseFloat(formData.target_value),
                target_unit: formData.target_unit,
                baseline_value: parseFloat(formData.baseline_value),
                baseline_year: formData.baseline_year,
                timeline_end_year: formData.timeline_end_year,
                emissions_scope: formData.emissions_scope,
                ticker: formData.ticker || undefined,
                documents: documents.length > 0 ? documents : undefined,
            })
        },
        onSuccess: (response) => {
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `KPI_Assessment_${formData.company_name.replace(/ /g, '_')}.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
        },
    })

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, docType: string) => {
        const files = e.target.files
        if (files && files[0]) {
            // Set the pending doc type BEFORE uploading so it's captured in onSuccess
            setPendingDocType(docType)
            setEvaluationError(null)
            uploadMutation.mutate(files[0])
        }
    }

    const handleInputChange = (field: string, value: string | number) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const canProceedToStep2 = formData.company_name && formData.industry_sector &&
        formData.target_value && formData.baseline_value

    const hasRequiredDocs = uploadedDocs.some(d => d.document_type === 'csrd_report') ||
        uploadedDocs.some(d => d.document_type === 'spts')

    const getRecommendationColor = (rec: string) => {
        switch (rec) {
            case 'APPROVE': return 'text-green-400'
            case 'CONDITIONAL_APPROVAL': return 'text-yellow-400'
            case 'NEGOTIATE': return 'text-orange-400'
            case 'REJECT': return 'text-red-400'
            default: return 'text-gray-400'
        }
    }

    const getAmbitionColor = (level: string) => {
        switch (level) {
            case 'SCIENCE_ALIGNED': return 'bg-green-500/20 text-green-400 border-green-500/50'
            case 'ABOVE_MARKET': return 'bg-blue-500/20 text-blue-400 border-blue-500/50'
            case 'MARKET_STANDARD': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
            case 'WEAK': return 'bg-red-500/20 text-red-400 border-red-500/50'
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50'
        }
    }

    const getCredibilityColor = (level: string) => {
        switch (level) {
            case 'HIGH': return 'text-green-400'
            case 'MEDIUM': return 'text-yellow-400'
            case 'LOW': return 'text-red-400'
            default: return 'text-gray-400'
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-3 bg-emerald-500/20 rounded-xl">
                            <Scale className="w-8 h-8 text-emerald-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                                KPI Benchmarking Engine
                            </h1>
                            <p className="text-gray-400">
                                Sustainability-Linked Loan Target Assessment
                            </p>
                        </div>
                    </div>
                    {statsData?.data && (
                        <div className="flex gap-4 mt-4 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                                <Users className="w-4 h-4" />
                                {statsData.data.companies_count?.toLocaleString() || 'Loading...'} SBTi Companies
                            </span>
                            <span className="flex items-center gap-1">
                                <Globe className="w-4 h-4" />
                                {statsData.data.sectors_available || 0} Sectors
                            </span>
                        </div>
                    )}
                </div>

                {/* Progress Steps */}
                <div className="flex items-center gap-4 mb-8">
                    {['Company & KPI', 'Documents', 'Review', 'Results'].map((label, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step > idx + 1 ? 'bg-emerald-500 text-white' :
                                step === idx + 1 ? 'bg-emerald-500/30 border-2 border-emerald-500 text-emerald-400' :
                                    'bg-gray-700 text-gray-500'
                                }`}>
                                {step > idx + 1 ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
                            </div>
                            <span className={step === idx + 1 ? 'text-white' : 'text-gray-500'}>{label}</span>
                            {idx < 3 && <ChevronRight className="w-4 h-4 text-gray-600" />}
                        </div>
                    ))}
                </div>

                {/* Step 1: Company & KPI Details */}
                {step === 1 && (
                    <div className="space-y-6">
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <Building2 className="w-5 h-5 text-emerald-400" />
                                Company Information
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Company Name *</label>
                                    <input
                                        type="text"
                                        value={formData.company_name}
                                        onChange={(e) => handleInputChange('company_name', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., TechCorp AG"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Industry Sector *</label>
                                    <input
                                        type="text"
                                        value={formData.industry_sector}
                                        onChange={(e) => handleInputChange('industry_sector', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., Technology Hardware"
                                        list="sectors-list"
                                    />
                                    <datalist id="sectors-list">
                                        {sectorsData?.data?.sectors?.slice(0, 20).map((s: string) => (
                                            <option key={s} value={s} />
                                        ))}
                                    </datalist>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Stock Ticker (Optional)</label>
                                    <input
                                        type="text"
                                        value={formData.ticker}
                                        onChange={(e) => handleInputChange('ticker', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., TCH.DE"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Facility Amount</label>
                                    <input
                                        type="text"
                                        value={formData.facility_amount}
                                        onChange={(e) => handleInputChange('facility_amount', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., €50,000,000"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <Target className="w-5 h-5 text-emerald-400" />
                                KPI Target Details
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Emissions Scope *</label>
                                    <select
                                        value={formData.emissions_scope}
                                        onChange={(e) => handleInputChange('emissions_scope', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                    >
                                        {EMISSION_SCOPES.map(s => (
                                            <option key={s.value} value={s.value}>{s.label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Baseline Value *</label>
                                    <input
                                        type="number"
                                        value={formData.baseline_value}
                                        onChange={(e) => handleInputChange('baseline_value', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., 250000"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Baseline Year</label>
                                    <input
                                        type="number"
                                        value={formData.baseline_year}
                                        onChange={(e) => handleInputChange('baseline_year', parseInt(e.target.value))}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Target Value (tCO2e) *</label>
                                    <input
                                        type="number"
                                        value={formData.target_value}
                                        onChange={(e) => handleInputChange('target_value', e.target.value)}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                        placeholder="e.g., 200000"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Target Year</label>
                                    <input
                                        type="number"
                                        value={formData.timeline_end_year}
                                        onChange={(e) => handleInputChange('timeline_end_year', parseInt(e.target.value))}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Margin Adjustment (bps)</label>
                                    <input
                                        type="number"
                                        value={formData.margin_adjustment_bps}
                                        onChange={(e) => handleInputChange('margin_adjustment_bps', parseInt(e.target.value))}
                                        className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
                                    />
                                </div>
                            </div>

                            {formData.baseline_value && formData.target_value && (
                                <div className="mt-4 p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                                    <div className="flex items-center gap-2 text-emerald-400">
                                        <TrendingUp className="w-5 h-5" />
                                        <span className="font-medium">
                                            Calculated Reduction: {((1 - parseFloat(formData.target_value) / parseFloat(formData.baseline_value)) * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex justify-end">
                            <button
                                onClick={() => setStep(2)}
                                disabled={!canProceedToStep2}
                                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                Next: Upload Documents
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 2: Document Upload */}
                {step === 2 && (
                    <div className="space-y-6">
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-emerald-400" />
                                Upload Evidence Documents
                            </h2>

                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
                                    <div>
                                        <p className="text-yellow-400 font-medium">Required Documents</p>
                                        <p className="text-sm text-gray-400">
                                            CSRD Report and SPTs document are mandatory for full assessment.
                                            Other documents enhance credibility scoring.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {DOCUMENT_TYPES.map((docType) => (
                                    <div
                                        key={docType.value}
                                        className={`border rounded-xl p-4 ${docType.mandatory ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-gray-600'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${docType.mandatory ? 'bg-emerald-500/20' : 'bg-gray-700'
                                                    }`}>
                                                    <FileCheck className={`w-5 h-5 ${docType.mandatory ? 'text-emerald-400' : 'text-gray-400'
                                                        }`} />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium">{docType.label}</span>
                                                        {docType.mandatory && (
                                                            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">
                                                                Required
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-gray-500">{docType.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                {uploadedDocs.find(d => d.document_type === docType.value) ? (
                                                    <div className="flex items-center gap-2 text-emerald-400">
                                                        <CheckCircle2 className="w-5 h-5" />
                                                        <span className="text-sm">
                                                            {uploadedDocs.find(d => d.document_type === docType.value)?.filename}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <label className="cursor-pointer">
                                                        <input
                                                            type="file"
                                                            accept=".pdf"
                                                            className="hidden"
                                                            onChange={(e) => handleFileUpload(e, docType.value)}
                                                        />
                                                        <div className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
                                                            <Upload className="w-4 h-4" />
                                                            <span className="text-sm">Upload PDF</span>
                                                        </div>
                                                    </label>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {uploadMutation.isPending && (
                                <div className="mt-4 flex items-center gap-2 text-gray-400">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Uploading and processing document...</span>
                                </div>
                            )}
                        </div>

                        <div className="flex justify-between">
                            <button
                                onClick={() => setStep(1)}
                                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={() => setStep(3)}
                                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                Next: Review & Submit
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 3: Review & Submit */}
                {step === 3 && (
                    <div className="space-y-6">
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <FileCheck className="w-5 h-5 text-emerald-400" />
                                Review Submission
                            </h2>

                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Company Details</h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Company</span>
                                            <span>{formData.company_name}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Sector</span>
                                            <span>{formData.industry_sector}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Ticker</span>
                                            <span>{formData.ticker || 'N/A'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Facility</span>
                                            <span>{formData.facility_amount || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">KPI Target</h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Scope</span>
                                            <span>{formData.emissions_scope}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Baseline</span>
                                            <span>{parseFloat(formData.baseline_value).toLocaleString()} tCO2e ({formData.baseline_year})</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Target</span>
                                            <span>{parseFloat(formData.target_value).toLocaleString()} tCO2e ({formData.timeline_end_year})</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Reduction</span>
                                            <span className="text-emerald-400 font-medium">
                                                {((1 - parseFloat(formData.target_value) / parseFloat(formData.baseline_value)) * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 pt-6 border-t border-gray-700">
                                <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Documents Uploaded</h3>
                                <div className="flex flex-wrap gap-2">
                                    {uploadedDocs.length > 0 ? uploadedDocs.map((doc, idx) => (
                                        <div key={idx} className="flex items-center gap-2 bg-gray-700/50 px-3 py-1.5 rounded-lg text-sm">
                                            <FileText className="w-4 h-4 text-emerald-400" />
                                            <span>{doc.filename}</span>
                                        </div>
                                    )) : (
                                        <span className="text-gray-500 text-sm">No documents uploaded (evaluation will use input data only)</span>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                            <div className="flex items-start gap-3">
                                <Info className="w-5 h-5 text-blue-400 mt-0.5" />
                                <div>
                                    <p className="text-blue-400 font-medium">What happens next?</p>
                                    <ul className="text-sm text-gray-400 mt-1 space-y-1">
                                        <li>• Your target will be benchmarked against SBTi peer companies</li>
                                        <li>• Credibility signals will be extracted from documents</li>
                                        <li>• Regulatory compliance will be checked (GLP, SLLP, SFDR, EBA)</li>
                                        <li>• A banker-ready assessment report will be generated</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Error Display */}
                        {evaluationError && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
                                    <div>
                                        <p className="text-red-400 font-medium">Error</p>
                                        <p className="text-sm text-gray-400 mt-1">{evaluationError}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="flex justify-between">
                            <button
                                onClick={() => setStep(2)}
                                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={() => evaluateMutation.mutate()}
                                disabled={evaluateMutation.isPending}
                                className="px-8 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-600 rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                {evaluateMutation.isPending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Running Evaluation...
                                    </>
                                ) : (
                                    <>
                                        <BarChart3 className="w-5 h-5" />
                                        Run Full Evaluation
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 4: Results */}
                {step === 4 && evaluationResult && (
                    <div className="space-y-6">
                        {/* Recommendation Banner */}
                        <div className={`rounded-2xl p-6 border ${evaluationResult.executive_summary.overall_recommendation === 'APPROVE'
                            ? 'bg-green-500/10 border-green-500/30'
                            : evaluationResult.executive_summary.overall_recommendation === 'CONDITIONAL_APPROVAL'
                                ? 'bg-yellow-500/10 border-yellow-500/30'
                                : 'bg-red-500/10 border-red-500/30'
                            }`}>
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <p className="text-sm text-gray-400 uppercase tracking-wider">Recommendation</p>
                                    <p className={`text-3xl font-bold ${getRecommendationColor(evaluationResult.executive_summary.overall_recommendation)}`}>
                                        {evaluationResult.executive_summary.overall_recommendation.replace(/_/g, ' ')}
                                    </p>
                                    <p className="text-gray-400 mt-2">
                                        {evaluationResult.executive_summary.recommendation_rationale}
                                    </p>
                                    {evaluationResult.executive_summary.ai_narrative && (
                                        <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                            <p className="text-sm text-blue-400 font-medium mb-2">AI Executive Summary</p>
                                            <p className="text-sm text-gray-300 leading-relaxed">{evaluationResult.executive_summary.ai_narrative}</p>
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={() => downloadPdfMutation.mutate()}
                                    disabled={downloadPdfMutation.isPending}
                                    className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg flex items-center gap-2 transition-colors"
                                >
                                    {downloadPdfMutation.isPending ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Download className="w-4 h-4" />
                                    )}
                                    Download PDF
                                </button>
                            </div>
                        </div>

                        {/* Key Findings */}
                        <div className="grid grid-cols-4 gap-4">
                            {evaluationResult.executive_summary.key_findings.map((finding, idx) => (
                                <div key={idx} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{finding.category}</p>
                                    <p className={`text-lg font-semibold ${finding.assessment === 'STRONG' || finding.assessment === 'HIGH' ? 'text-green-400' :
                                        finding.assessment === 'WEAK' || finding.assessment === 'LOW' ? 'text-red-400' :
                                            'text-yellow-400'
                                        }`}>
                                        {finding.assessment}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">{finding.detail.substring(0, 50)}...</p>
                                </div>
                            ))}
                        </div>

                        {/* Peer Benchmarking */}
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Users className="w-5 h-5 text-emerald-400" />
                                Peer Benchmarking
                            </h3>
                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-gray-400">Peers Analyzed</span>
                                        <span className="font-medium">
                                            {evaluationResult.peer_benchmarking.peer_statistics.peer_count} companies
                                            <span className={`ml-2 text-xs px-2 py-0.5 rounded ${evaluationResult.peer_benchmarking.peer_statistics.confidence_level === 'HIGH'
                                                ? 'bg-green-500/20 text-green-400'
                                                : 'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                {evaluationResult.peer_benchmarking.peer_statistics.confidence_level}
                                            </span>
                                        </span>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <span className="text-gray-500">Peer Median</span>
                                            <span>{evaluationResult.peer_benchmarking.peer_statistics.percentiles.median?.toFixed(1)}%</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-gray-500">75th Percentile</span>
                                            <span>{evaluationResult.peer_benchmarking.peer_statistics.percentiles.p75?.toFixed(1)}%</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-gray-500">Your Position</span>
                                            <span>Percentile {evaluationResult.peer_benchmarking.company_position.percentile_rank}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center justify-center">
                                    <div className={`px-6 py-4 rounded-xl border-2 ${getAmbitionColor(evaluationResult.peer_benchmarking.ambition_classification.level)}`}>
                                        <p className="text-xs text-center mb-1">Ambition Level</p>
                                        <p className="text-2xl font-bold text-center">
                                            {evaluationResult.peer_benchmarking.ambition_classification.level.replace(/_/g, ' ')}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            {evaluationResult.peer_benchmarking.ambition_classification.ai_detailed_analysis && (
                                <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                                    <p className="text-sm text-emerald-400 font-medium mb-2">AI Ambition Analysis</p>
                                    <p className="text-sm text-gray-300 leading-relaxed">{evaluationResult.peer_benchmarking.ambition_classification.ai_detailed_analysis}</p>
                                    {evaluationResult.peer_benchmarking.ambition_classification.classification_explanation && (
                                        <p className="text-xs text-gray-400 mt-2 italic">{evaluationResult.peer_benchmarking.ambition_classification.classification_explanation}</p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Credibility Signals */}
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-emerald-400" />
                                Credibility Assessment
                                <span className={`ml-2 text-sm font-normal ${getCredibilityColor(evaluationResult.achievability_assessment.credibility_level)}`}>
                                    ({evaluationResult.achievability_assessment.credibility_level} Credibility)
                                </span>
                            </h3>
                            {evaluationResult.achievability_assessment.ai_detailed_analysis && (
                                <div className="mb-4 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                                    <p className="text-sm text-purple-400 font-medium mb-2">AI Credibility Analysis</p>
                                    <p className="text-sm text-gray-300 leading-relaxed">{evaluationResult.achievability_assessment.ai_detailed_analysis}</p>
                                </div>
                            )}
                            <div className="grid grid-cols-3 gap-4">
                                {Object.entries(evaluationResult.achievability_assessment.signals).map(([key, value]) => (
                                    <div key={key} className="flex items-center gap-3 p-3 bg-gray-700/30 rounded-lg">
                                        {value.detected ? (
                                            <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                                        )}
                                        <span className="text-sm">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Risk Flags */}
                        {evaluationResult.risk_flags.length > 0 && (
                            <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                                    Risk Flags
                                </h3>
                                <div className="space-y-3">
                                    {evaluationResult.risk_flags.map((flag, idx) => (
                                        <div key={idx} className={`p-4 rounded-lg border ${flag.severity === 'HIGH' ? 'bg-red-500/10 border-red-500/30' :
                                            flag.severity === 'MEDIUM' ? 'bg-yellow-500/10 border-yellow-500/30' :
                                                'bg-blue-500/10 border-blue-500/30'
                                            }`}>
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <p className="font-medium">{flag.issue}</p>
                                                    <p className="text-sm text-gray-400 mt-1">{flag.recommendation}</p>
                                                </div>
                                                <span className={`text-xs px-2 py-1 rounded ${flag.severity === 'HIGH' ? 'bg-red-500/30 text-red-400' :
                                                    flag.severity === 'MEDIUM' ? 'bg-yellow-500/30 text-yellow-400' :
                                                        'bg-blue-500/30 text-blue-400'
                                                    }`}>
                                                    {flag.severity}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Regulatory Compliance */}
                        <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Award className="w-5 h-5 text-emerald-400" />
                                Regulatory Compliance
                            </h3>
                            <div className="grid grid-cols-4 gap-4">
                                {Object.entries(evaluationResult.regulatory_compliance.summary).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                                        <span className="text-sm">{key.replace(/_/g, ' ').toUpperCase()}</span>
                                        {value ? (
                                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-red-400" />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Conditions */}
                        {evaluationResult.final_decision.conditions.length > 0 && (
                            <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                                <h3 className="text-lg font-semibold mb-4">Conditions for Approval</h3>
                                <div className="space-y-3">
                                    {evaluationResult.final_decision.conditions.map((cond, idx) => (
                                        <div key={idx} className="flex items-start gap-3 p-3 bg-gray-700/30 rounded-lg">
                                            <span className={`text-xs px-2 py-1 rounded ${cond.priority === 'HIGH' ? 'bg-red-500/30 text-red-400' : 'bg-yellow-500/30 text-yellow-400'
                                                }`}>
                                                {cond.priority}
                                            </span>
                                            <div>
                                                <p className="font-medium">{cond.condition}</p>
                                                <p className="text-sm text-gray-400">{cond.detail}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex justify-between">
                            <button
                                onClick={() => {
                                    setStep(1)
                                    setEvaluationResult(null)
                                    setUploadedDocs([])
                                    setFormData({
                                        company_name: '',
                                        industry_sector: '',
                                        metric: 'GHG Emissions Reduction',
                                        target_value: '',
                                        target_unit: 'tCO2e',
                                        baseline_value: '',
                                        baseline_year: new Date().getFullYear() - 1,
                                        timeline_end_year: 2030,
                                        emissions_scope: 'Scope 1+2',
                                        ticker: '',
                                        facility_amount: '',
                                        tenor_years: 5,
                                        margin_adjustment_bps: 15,
                                        loan_type: 'Sustainability-Linked Loan',
                                    })
                                }}
                                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium flex items-center gap-2 transition-colors"
                            >
                                New Evaluation
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
