import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiEvaluationApi } from '@/lib/api'
import {
    Loader2, Target, TrendingUp, FileText, Upload,
    CheckCircle2, XCircle, AlertTriangle, ChevronRight, Plus,
    Building2, Scale, FileCheck
} from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'
import { KobaltInput } from '@/components/ui/KobaltInput'

type EvaluationStep = 'form' | 'documents' | 'running' | 'result'

interface EvaluationResult {
    id: number
    company_name: string
    metric: string
    status: string
    assessment_grade?: string
    success_probability?: number
    result_summary?: string
    needs_review: boolean
    banker_decision: string
    created_at: string
}

const METRICS = [
    { value: 'carbon_reduction', label: 'Carbon Reduction' },
    { value: 'renewable_energy_increase', label: 'Renewable Energy Increase' },
    { value: 'water_reduction', label: 'Water Reduction' },
    { value: 'waste_recycling', label: 'Waste Recycling' },
    { value: 'women_leadership', label: 'Women in Leadership' },
    { value: 'safety_incident_rate', label: 'Safety Incident Rate' },
]

const SECTORS = [
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'financial_services', label: 'Financial Services' },
    { value: 'real_estate', label: 'Real Estate' },
    { value: 'transportation', label: 'Transportation' },
    { value: 'technology', label: 'Technology' },
    { value: 'energy', label: 'Energy' },
    { value: 'healthcare', label: 'Healthcare' },
]

const REGIONS = [
    { value: 'EU', label: 'European Union' },
    { value: 'non-EU', label: 'Non-EU' },
    { value: 'US', label: 'United States' },
    { value: 'APAC', label: 'Asia Pacific' },
]

const VERIFICATION_TYPES = [
    { value: 'audited', label: 'Audited' },
    { value: 'third_party_verified', label: 'Third Party Verified' },
    { value: 'self_reported', label: 'Self Reported' },
    { value: 'unknown', label: 'Unknown' },
]

export default function KPITool() {
    const queryClient = useQueryClient()
    const [step, setStep] = useState<EvaluationStep>('form')
    const [currentEvaluationId, setCurrentEvaluationId] = useState<number | null>(null)
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
    const [showHistory, setShowHistory] = useState(false)

    // Form state
    const [formData, setFormData] = useState({
        loan_reference_id: '',
        company_name: '',
        industry_sector: '',
        region: 'EU',
        metric: '',
        target_value: 0,
        target_unit: '%',
        timeline_start_year: new Date().getFullYear(),
        timeline_end_year: new Date().getFullYear() + 3,
        baseline_value: 0,
        baseline_unit: '%',
        baseline_year: new Date().getFullYear() - 1,
        baseline_verification: 'unknown',
        company_size_proxy: '',
        emissions_scope: '',
        methodology: '',
        capex_budget: '',
        plan_description: '',
        csrd_reporting_status: 'unknown',
    })

    // Fetch evaluation history
    const { data: evaluationsData } = useQuery({
        queryKey: ['kpi-evaluations'],
        queryFn: () => kpiEvaluationApi.list(),
    })

    // Fetch single evaluation result
    const { data: evaluationResult, isLoading: isLoadingResult } = useQuery({
        queryKey: ['kpi-evaluation', currentEvaluationId],
        queryFn: () => kpiEvaluationApi.get(currentEvaluationId!),
        enabled: !!currentEvaluationId && step === 'result',
    })

    // Create evaluation mutation
    const createMutation = useMutation({
        mutationFn: () => kpiEvaluationApi.create(formData),
        onSuccess: (response) => {
            setCurrentEvaluationId(response.data.id)
            setStep('documents')
        },
    })

    // Attach documents mutation
    const attachDocsMutation = useMutation({
        mutationFn: () => kpiEvaluationApi.attachDocuments(currentEvaluationId!, uploadedFiles),
        onSuccess: () => {
            runMutation.mutate()
            setStep('running')
        },
    })

    // Run verification mutation
    const runMutation = useMutation({
        mutationFn: () => kpiEvaluationApi.run(currentEvaluationId!),
        onSuccess: () => {
            setStep('result')
            queryClient.invalidateQueries({ queryKey: ['kpi-evaluations'] })
        },
    })

    // Submit decision mutation
    const decisionMutation = useMutation({
        mutationFn: ({ decision, reason }: { decision: string; reason?: string }) =>
            kpiEvaluationApi.submitDecision(currentEvaluationId!, decision, reason),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['kpi-evaluation', currentEvaluationId] })
            queryClient.invalidateQueries({ queryKey: ['kpi-evaluations'] })
        },
    })

    const handleInputChange = (field: string, value: string | number) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setUploadedFiles(Array.from(e.target.files))
        }
    }

    const handleSubmitForm = () => {
        createMutation.mutate()
    }

    const handleSubmitDocuments = () => {
        if (uploadedFiles.length > 0) {
            attachDocsMutation.mutate()
        } else {
            // Skip document upload, run directly
            runMutation.mutate()
            setStep('running')
        }
    }

    const handleDecision = (decision: string) => {
        decisionMutation.mutate({ decision })
    }

    const resetForm = () => {
        setStep('form')
        setCurrentEvaluationId(null)
        setUploadedFiles([])
        setFormData({
            loan_reference_id: '',
            company_name: '',
            industry_sector: '',
            region: 'EU',
            metric: '',
            target_value: 0,
            target_unit: '%',
            timeline_start_year: new Date().getFullYear(),
            timeline_end_year: new Date().getFullYear() + 3,
            baseline_value: 0,
            baseline_unit: '%',
            baseline_year: new Date().getFullYear() - 1,
            baseline_verification: 'unknown',
            company_size_proxy: '',
            emissions_scope: '',
            methodology: '',
            capex_budget: '',
            plan_description: '',
            csrd_reporting_status: 'unknown',
        })
    }

    const getGradeColor = (grade?: string) => {
        switch (grade) {
            case 'AMBITIOUS': return 'text-green-600 bg-green-50'
            case 'MODERATE': return 'text-yellow-600 bg-yellow-50'
            case 'WEAK': return 'text-red-600 bg-red-50'
            default: return 'text-kobalt-black/60 bg-kobalt-gray'
        }
    }

    const evaluations = evaluationsData?.data || []

    return (
        <div className="space-y-6 animate-fade-in pb-12">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-kobalt-black">KPI Target Evaluation</h1>
                    <p className="text-kobalt-black/60">Evaluate borrower sustainability targets against industry benchmarks</p>
                </div>
                <div className="flex gap-2">
                    <KobaltButton
                        variant="secondary"
                        onClick={() => setShowHistory(!showHistory)}
                        className="flex items-center gap-2"
                    >
                        {showHistory ? 'New Evaluation' : 'View History'}
                    </KobaltButton>
                    {step !== 'form' && (
                        <KobaltButton
                            onClick={resetForm}
                            className="flex items-center gap-2"
                        >
                            <Plus className="w-4 h-4" /> New Evaluation
                        </KobaltButton>
                    )}
                </div>
            </div>

            {/* Progress Steps */}
            {!showHistory && (
                <div className="flex items-center gap-2 mb-6">
                    {['form', 'documents', 'running', 'result'].map((s, i) => (
                        <div key={s} className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${step === s ? 'bg-kobalt-blue text-white' :
                                ['form', 'documents', 'running', 'result'].indexOf(step) > i ? 'bg-green-500 text-white' :
                                    'bg-kobalt-gray text-kobalt-black/40'
                                }`}>
                                {['form', 'documents', 'running', 'result'].indexOf(step) > i ? '✓' : i + 1}
                            </div>
                            {i < 3 && <ChevronRight className="w-4 h-4 mx-2 text-kobalt-black/30" />}
                        </div>
                    ))}
                    <span className="ml-4 text-sm font-medium text-kobalt-black/60">
                        {step === 'form' && 'Enter Target Details'}
                        {step === 'documents' && 'Upload Supporting Documents'}
                        {step === 'running' && 'AI Verification in Progress'}
                        {step === 'result' && 'Review Assessment'}
                    </span>
                </div>
            )}

            {/* History View */}
            {showHistory && (
                <KobaltCard className="border-kobalt-border overflow-hidden p-0">
                    <div className="p-4 border-b border-kobalt-border bg-kobalt-gray/30">
                        <h3 className="font-semibold text-kobalt-black">Evaluation History</h3>
                    </div>
                    <div className="divide-y divide-kobalt-border">
                        {evaluations.length === 0 ? (
                            <div className="p-8 text-center text-kobalt-black/50">
                                No evaluations yet. Start by creating a new evaluation.
                            </div>
                        ) : (
                            evaluations.map((evaluation: EvaluationResult) => (
                                <div key={evaluation.id} className="p-4 hover:bg-kobalt-gray/50 cursor-pointer transition-colors" onClick={() => {
                                    setCurrentEvaluationId(evaluation.id)
                                    setStep('result')
                                    setShowHistory(false)
                                }}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium text-kobalt-black">{evaluation.company_name}</p>
                                            <p className="text-sm text-kobalt-black/60 capitalize">{evaluation.metric.replace(/_/g, ' ')}</p>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {evaluation.assessment_grade && (
                                                <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide ${getGradeColor(evaluation.assessment_grade)}`}>
                                                    {evaluation.assessment_grade}
                                                </span>
                                            )}
                                            <span className="text-sm text-kobalt-black/50">
                                                {new Date(evaluation.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </KobaltCard>
            )}

            {/* Step 1: Input Form */}
            {!showHistory && step === 'form' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Required Fields */}
                    <KobaltCard className="space-y-5">
                        <h3 className="font-semibold flex items-center gap-2 text-lg text-kobalt-black border-b border-kobalt-border pb-3 mb-2">
                            <Target className="w-5 h-5 text-kobalt-blue" />
                            Target Details (Required)
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <KobaltInput
                                label="Loan Reference ID"
                                value={formData.loan_reference_id}
                                onChange={(e) => handleInputChange('loan_reference_id', e.target.value)}
                                placeholder="e.g., LOAN-2024-001"
                            />
                            <KobaltInput
                                label="Company Name"
                                value={formData.company_name}
                                onChange={(e) => handleInputChange('company_name', e.target.value)}
                                placeholder="e.g., Acme Corp"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Industry Sector</label>
                                <select
                                    value={formData.industry_sector}
                                    onChange={(e) => handleInputChange('industry_sector', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    <option value="">Select sector...</option>
                                    {SECTORS.map(s => (
                                        <option key={s.value} value={s.value}>{s.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Region</label>
                                <select
                                    value={formData.region}
                                    onChange={(e) => handleInputChange('region', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    {REGIONS.map(r => (
                                        <option key={r.value} value={r.value}>{r.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">KPI Metric</label>
                            <select
                                value={formData.metric}
                                onChange={(e) => handleInputChange('metric', e.target.value)}
                                className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                            >
                                <option value="">Select metric...</option>
                                {METRICS.map(m => (
                                    <option key={m.value} value={m.value}>{m.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Target Value</label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        value={formData.target_value}
                                        onChange={(e) => handleInputChange('target_value', parseFloat(e.target.value))}
                                        className="flex-1 bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                        placeholder="e.g., 30"
                                    />
                                    <select
                                        value={formData.target_unit}
                                        onChange={(e) => handleInputChange('target_unit', e.target.value)}
                                        className="w-24 bg-kobalt-gray/50 border border-transparent rounded-xl px-2 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                    >
                                        <option value="%">%</option>
                                        <option value="tCO2e">tCO2e</option>
                                        <option value="MWh">MWh</option>
                                    </select>
                                </div>
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Timeline</label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number"
                                        value={formData.timeline_start_year}
                                        onChange={(e) => handleInputChange('timeline_start_year', parseInt(e.target.value))}
                                        className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-3 py-3 text-center text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                    />
                                    <span className="text-kobalt-black/50">to</span>
                                    <input
                                        type="number"
                                        value={formData.timeline_end_year}
                                        onChange={(e) => handleInputChange('timeline_end_year', parseInt(e.target.value))}
                                        className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-3 py-3 text-center text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            <KobaltInput
                                label="Baseline Value"
                                type="number"
                                value={formData.baseline_value}
                                onChange={(e) => handleInputChange('baseline_value', parseFloat(e.target.value))}
                            />
                            <KobaltInput
                                label="Baseline Year"
                                type="number"
                                value={formData.baseline_year}
                                onChange={(e) => handleInputChange('baseline_year', parseInt(e.target.value))}
                            />
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Verification</label>
                                <select
                                    value={formData.baseline_verification}
                                    onChange={(e) => handleInputChange('baseline_verification', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    {VERIFICATION_TYPES.map(v => (
                                        <option key={v.value} value={v.value}>{v.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </KobaltCard>

                    {/* Optional Fields */}
                    <KobaltCard className="space-y-5">
                        <h3 className="font-semibold flex items-center gap-2 text-lg text-kobalt-black border-b border-kobalt-border pb-3 mb-2">
                            <Building2 className="w-5 h-5 text-kobalt-blue" />
                            Additional Context (Optional)
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Company Size</label>
                                <select
                                    value={formData.company_size_proxy}
                                    onChange={(e) => handleInputChange('company_size_proxy', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    <option value="">Select size...</option>
                                    <option value="small">Small (&lt;€50M revenue)</option>
                                    <option value="medium">Medium (€50M-€500M)</option>
                                    <option value="large">Large (€500M-€5B)</option>
                                    <option value="enterprise">Enterprise (&gt;€5B)</option>
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Emissions Scope</label>
                                <select
                                    value={formData.emissions_scope}
                                    onChange={(e) => handleInputChange('emissions_scope', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    <option value="">Select scope...</option>
                                    <option value="scope_1_2">Scope 1 + 2</option>
                                    <option value="scope_3">Scope 3</option>
                                    <option value="all">All Scopes</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Methodology</label>
                                <select
                                    value={formData.methodology}
                                    onChange={(e) => handleInputChange('methodology', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    <option value="">Select methodology...</option>
                                    <option value="baseline_year">Baseline Year</option>
                                    <option value="yoy">Year-over-Year</option>
                                    <option value="intensity">Intensity-based</option>
                                    <option value="absolute">Absolute Target</option>
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">CSRD Reporting</label>
                                <select
                                    value={formData.csrd_reporting_status}
                                    onChange={(e) => handleInputChange('csrd_reporting_status', e.target.value)}
                                    className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200"
                                >
                                    <option value="unknown">Unknown</option>
                                    <option value="yes">Yes</option>
                                    <option value="no">No</option>
                                    <option value="in_progress">In Progress</option>
                                </select>
                            </div>
                        </div>

                        <KobaltInput
                            label="CapEx Budget (if known)"
                            value={formData.capex_budget}
                            onChange={(e) => handleInputChange('capex_budget', e.target.value)}
                            placeholder="e.g., €10M sustainability investment"
                        />

                        <div className="space-y-1.5">
                            <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">Implementation Plan Description</label>
                            <textarea
                                value={formData.plan_description}
                                onChange={(e) => handleInputChange('plan_description', e.target.value)}
                                rows={3}
                                className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none transition-all duration-200 resize-none"
                                placeholder="Briefly describe how the company plans to achieve this target..."
                            />
                        </div>

                        <KobaltButton
                            onClick={handleSubmitForm}
                            disabled={!formData.company_name || !formData.industry_sector || !formData.metric || createMutation.isPending}
                            className="w-full mt-4"
                            isLoading={createMutation.isPending}
                        >
                            Continue to Document Upload
                            <ChevronRight className="w-4 h-4 ml-2" />
                        </KobaltButton>
                    </KobaltCard>
                </div>
            )}

            {/* Step 2: Document Upload */}
            {!showHistory && step === 'documents' && (
                <div className="max-w-2xl mx-auto">
                    <KobaltCard className="p-8 text-center space-y-8">
                        <div>
                            <div className="w-16 h-16 bg-kobalt-blue/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Upload className="w-8 h-8 text-kobalt-blue" />
                            </div>
                            <h3 className="text-xl font-bold text-kobalt-black">Upload Supporting Documents</h3>
                            <p className="text-kobalt-black/60 mt-2 max-w-sm mx-auto">
                                Upload CSRD sustainability statements, ESG reports, or SPO documents for AI verification
                            </p>
                        </div>

                        <div className="border-2 border-dashed border-kobalt-border rounded-2xl p-10 hover:border-kobalt-blue/50 hover:bg-kobalt-blue/5 transition-all duration-300">
                            <input
                                type="file"
                                multiple
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="hidden"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer block">
                                <FileText className="w-12 h-12 text-kobalt-black/40 mx-auto mb-4" />
                                <p className="font-semibold text-kobalt-black text-lg">Click to upload PDF documents</p>
                                <p className="text-sm text-kobalt-black/50 mt-1">or drag and drop</p>
                            </label>
                        </div>

                        {uploadedFiles.length > 0 && (
                            <div className="bg-kobalt-gray/50 rounded-xl p-4 text-left">
                                <p className="text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider mb-2">Selected Files</p>
                                <div className="space-y-2">
                                    {uploadedFiles.map((file, i) => (
                                        <div key={i} className="flex items-center gap-2 text-sm bg-white border border-kobalt-border rounded-lg px-3 py-2">
                                            <FileCheck className="w-4 h-4 text-green-500" />
                                            {file.name}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-1 gap-4">
                            <KobaltButton
                                onClick={handleSubmitDocuments}
                                disabled={attachDocsMutation.isPending || runMutation.isPending}
                                isLoading={attachDocsMutation.isPending || runMutation.isPending}
                                className="w-full"
                            >
                                {uploadedFiles.length > 0 ? 'Upload & Run Verification' : 'Skip & Run Verification'}
                            </KobaltButton>
                        </div>
                    </KobaltCard>
                </div>
            )}

            {/* Step 3: Running */}
            {!showHistory && step === 'running' && (
                <div className="max-w-xl mx-auto text-center py-12">
                    <KobaltCard className="p-12">
                        <Loader2 className="w-16 h-16 text-kobalt-blue mx-auto mb-6 animate-spin" />
                        <h3 className="text-xl font-bold text-kobalt-black mb-2">AI Verification in Progress</h3>
                        <p className="text-kobalt-black/60">
                            Analyzing target against industry benchmarks, extracting evidence from documents, and generating assessment...
                        </p>
                        <div className="mt-8 space-y-3 text-sm text-left max-w-xs mx-auto">
                            <div className="flex items-center gap-3 text-kobalt-black/70">
                                <CheckCircle2 className="w-5 h-5 text-green-500" /> Input validation complete
                            </div>
                            <div className="flex items-center gap-3 text-kobalt-black/70">
                                <Loader2 className="w-5 h-5 animate-spin text-kobalt-blue" /> Extracting document evidence...
                            </div>
                            <div className="flex items-center gap-3 text-kobalt-black/40">
                                <div className="w-5 h-5 rounded-full border-2 border-kobalt-black/10" /> Searching industry benchmarks
                            </div>
                            <div className="flex items-center gap-3 text-kobalt-black/40">
                                <div className="w-5 h-5 rounded-full border-2 border-kobalt-black/10" /> Computing assessment score
                            </div>
                        </div>
                    </KobaltCard>
                </div>
            )}

            {/* Step 4: Results */}
            {!showHistory && step === 'result' && (
                <div className="space-y-6">
                    {isLoadingResult ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto text-kobalt-blue" />
                        </div>
                    ) : evaluationResult?.data ? (
                        <>
                            {/* Assessment Header */}
                            <KobaltCard className="p-8 bg-gradient-to-br from-kobalt-blue/5 to-transparent border-kobalt-blue/20">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h1 className="text-2xl font-bold text-kobalt-black">{evaluationResult.data.company_name}</h1>
                                        <p className="text-kobalt-black/60 mt-1 capitalize">{evaluationResult.data.metric?.replace(/_/g, ' ')}</p>
                                    </div>
                                    <div className={`px-6 py-3 rounded-xl text-xl font-bold tracking-tight shadow-sm border ${getGradeColor(evaluationResult.data.assessment_grade).replace('bg-opacity-10', 'bg-opacity-20')}`}>
                                        {evaluationResult.data.assessment_grade || 'PENDING'}
                                    </div>
                                </div>
                            </KobaltCard>

                            {/* Results Grid */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <KobaltCard>
                                    <div className="flex items-center gap-2 mb-3 text-kobalt-black/60">
                                        <Scale className="w-5 h-5 text-kobalt-blue" />
                                        <span className="font-medium">Success Probability</span>
                                    </div>
                                    <p className="text-4xl font-bold text-kobalt-black tracking-tight leading-none">
                                        {((evaluationResult.data.success_probability || 0) * 100).toFixed(0)}%
                                    </p>
                                    <div className="w-full bg-kobalt-gray h-2 rounded-full mt-4 overflow-hidden">
                                        <div
                                            className="h-full bg-kobalt-blue rounded-full transition-all duration-1000"
                                            style={{ width: `${(evaluationResult.data.success_probability || 0) * 100}%` }}
                                        />
                                    </div>
                                </KobaltCard>
                                <KobaltCard>
                                    <div className="flex items-center gap-2 mb-3 text-kobalt-black/60">
                                        <Target className="w-5 h-5 text-kobalt-blue" />
                                        <span className="font-medium">Status</span>
                                    </div>
                                    <p className="text-2xl font-bold text-kobalt-black capitalize">{evaluationResult.data.status}</p>
                                </KobaltCard>
                                <KobaltCard>
                                    <div className="flex items-center gap-2 mb-3 text-kobalt-black/60">
                                        {evaluationResult.data.needs_review ? (
                                            <AlertTriangle className="w-5 h-5 text-yellow-500" />
                                        ) : (
                                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                                        )}
                                        <span className="font-medium">Review Status</span>
                                    </div>
                                    <p className="text-2xl font-bold text-kobalt-black">
                                        {evaluationResult.data.needs_review ? 'Needs Review' : 'Ready for Decision'}
                                    </p>
                                </KobaltCard>
                            </div>

                            {/* Summary */}
                            {evaluationResult.data.result_summary && (
                                <KobaltCard>
                                    <h4 className="font-bold mb-4 flex items-center gap-2 text-kobalt-black text-lg">
                                        <TrendingUp className="w-5 h-5 text-kobalt-blue" />
                                        AI Assessment Summary
                                    </h4>
                                    <p className="text-kobalt-black/70 leading-relaxed text-lg">{evaluationResult.data.result_summary}</p>
                                </KobaltCard>
                            )}

                            {/* Banker Decision */}
                            {evaluationResult.data.banker_decision === 'PENDING' && (
                                <KobaltCard className="border-kobalt-blue/20 bg-kobalt-blue/5">
                                    <h4 className="font-bold mb-4 text-kobalt-black">Submit Your Decision</h4>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => handleDecision('ACCEPT_AS_IS')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 hover:shadow-lg transition-all flex items-center justify-center gap-2"
                                        >
                                            <CheckCircle2 className="w-5 h-5" /> Accept
                                        </button>
                                        <button
                                            onClick={() => handleDecision('NEGOTIATE')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-yellow-600 text-white rounded-xl font-medium hover:bg-yellow-700 hover:shadow-lg transition-all flex items-center justify-center gap-2"
                                        >
                                            <AlertTriangle className="w-5 h-5" /> Negotiate
                                        </button>
                                        <button
                                            onClick={() => handleDecision('REJECT')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-red-600 text-white rounded-xl font-medium hover:bg-red-700 hover:shadow-lg transition-all flex items-center justify-center gap-2"
                                        >
                                            <XCircle className="w-5 h-5" /> Reject
                                        </button>
                                    </div>
                                </KobaltCard>
                            )}

                            {evaluationResult.data.banker_decision !== 'PENDING' && (
                                <KobaltCard className="border-green-500/30 bg-green-50">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                                            <CheckCircle2 className="w-6 h-6 text-green-600" />
                                        </div>
                                        <div>
                                            <span className="font-semibold text-green-900 block">Decision Recorded</span>
                                            <span className="text-green-700">{evaluationResult.data.banker_decision}</span>
                                        </div>
                                    </div>
                                </KobaltCard>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-12 text-kobalt-black/50">
                            No evaluation data found.
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
