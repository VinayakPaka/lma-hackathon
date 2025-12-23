import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi, kpiEvaluationApi } from '@/lib/api'
import {
    BarChart3, Loader2, Target, TrendingUp, FileText, Upload,
    CheckCircle2, XCircle, AlertTriangle, ChevronRight, Plus,
    Building2, Calendar, Percent, Scale, FileCheck
} from 'lucide-react'

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
            case 'AMBITIOUS': return 'text-green-500 bg-green-500/10'
            case 'MODERATE': return 'text-yellow-500 bg-yellow-500/10'
            case 'WEAK': return 'text-red-500 bg-red-500/10'
            default: return 'text-muted-foreground bg-muted'
        }
    }

    const evaluations = evaluationsData?.data || []

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">KPI Target Evaluation</h1>
                    <p className="text-muted-foreground">Evaluate borrower sustainability targets against industry benchmarks</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
                    >
                        {showHistory ? 'New Evaluation' : 'View History'}
                    </button>
                    {step !== 'form' && (
                        <button
                            onClick={resetForm}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
                        >
                            <Plus className="w-4 h-4" /> New Evaluation
                        </button>
                    )}
                </div>
            </div>

            {/* Progress Steps */}
            {!showHistory && (
                <div className="flex items-center gap-2 mb-6">
                    {['form', 'documents', 'running', 'result'].map((s, i) => (
                        <div key={s} className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === s ? 'bg-primary text-primary-foreground' :
                                    ['form', 'documents', 'running', 'result'].indexOf(step) > i ? 'bg-green-500 text-white' :
                                        'bg-muted text-muted-foreground'
                                }`}>
                                {['form', 'documents', 'running', 'result'].indexOf(step) > i ? '✓' : i + 1}
                            </div>
                            {i < 3 && <ChevronRight className="w-4 h-4 mx-2 text-muted-foreground" />}
                        </div>
                    ))}
                    <span className="ml-4 text-sm text-muted-foreground">
                        {step === 'form' && 'Enter Target Details'}
                        {step === 'documents' && 'Upload Supporting Documents'}
                        {step === 'running' && 'AI Verification in Progress'}
                        {step === 'result' && 'Review Assessment'}
                    </span>
                </div>
            )}

            {/* History View */}
            {showHistory && (
                <div className="bg-card rounded-xl border border-border">
                    <div className="p-4 border-b border-border">
                        <h3 className="font-semibold">Evaluation History</h3>
                    </div>
                    <div className="divide-y divide-border">
                        {evaluations.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                No evaluations yet. Start by creating a new evaluation.
                            </div>
                        ) : (
                            evaluations.map((evaluation: EvaluationResult) => (
                                <div key={evaluation.id} className="p-4 hover:bg-muted/50 cursor-pointer" onClick={() => {
                                    setCurrentEvaluationId(evaluation.id)
                                    setStep('result')
                                    setShowHistory(false)
                                }}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium">{evaluation.company_name}</p>
                                            <p className="text-sm text-muted-foreground">{evaluation.metric.replace(/_/g, ' ')}</p>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {evaluation.assessment_grade && (
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(evaluation.assessment_grade)}`}>
                                                    {evaluation.assessment_grade}
                                                </span>
                                            )}
                                            <span className="text-sm text-muted-foreground">
                                                {new Date(evaluation.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Step 1: Input Form */}
            {!showHistory && step === 'form' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Required Fields */}
                    <div className="bg-card rounded-xl p-6 border border-border space-y-4">
                        <h3 className="font-semibold flex items-center gap-2 text-lg">
                            <Target className="w-5 h-5 text-primary" />
                            Target Details (Required)
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Loan Reference ID</label>
                                <input
                                    type="text"
                                    value={formData.loan_reference_id}
                                    onChange={(e) => handleInputChange('loan_reference_id', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    placeholder="e.g., LOAN-2024-001"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Company Name</label>
                                <input
                                    type="text"
                                    value={formData.company_name}
                                    onChange={(e) => handleInputChange('company_name', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    placeholder="e.g., Acme Corp"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Industry Sector</label>
                                <select
                                    value={formData.industry_sector}
                                    onChange={(e) => handleInputChange('industry_sector', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                >
                                    <option value="">Select sector...</option>
                                    {SECTORS.map(s => (
                                        <option key={s.value} value={s.value}>{s.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Region</label>
                                <select
                                    value={formData.region}
                                    onChange={(e) => handleInputChange('region', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                >
                                    {REGIONS.map(r => (
                                        <option key={r.value} value={r.value}>{r.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">KPI Metric</label>
                            <select
                                value={formData.metric}
                                onChange={(e) => handleInputChange('metric', e.target.value)}
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="">Select metric...</option>
                                {METRICS.map(m => (
                                    <option key={m.value} value={m.value}>{m.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Target Value</label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        value={formData.target_value}
                                        onChange={(e) => handleInputChange('target_value', parseFloat(e.target.value))}
                                        className="flex-1 px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                        placeholder="e.g., 30"
                                    />
                                    <select
                                        value={formData.target_unit}
                                        onChange={(e) => handleInputChange('target_unit', e.target.value)}
                                        className="w-20 px-2 py-2.5 bg-muted rounded-lg border border-border"
                                    >
                                        <option value="%">%</option>
                                        <option value="tCO2e">tCO2e</option>
                                        <option value="MWh">MWh</option>
                                    </select>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Timeline</label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number"
                                        value={formData.timeline_start_year}
                                        onChange={(e) => handleInputChange('timeline_start_year', parseInt(e.target.value))}
                                        className="w-24 px-3 py-2.5 bg-muted rounded-lg border border-border"
                                    />
                                    <span>to</span>
                                    <input
                                        type="number"
                                        value={formData.timeline_end_year}
                                        onChange={(e) => handleInputChange('timeline_end_year', parseInt(e.target.value))}
                                        className="w-24 px-3 py-2.5 bg-muted rounded-lg border border-border"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Baseline Value</label>
                                <input
                                    type="number"
                                    value={formData.baseline_value}
                                    onChange={(e) => handleInputChange('baseline_value', parseFloat(e.target.value))}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Baseline Year</label>
                                <input
                                    type="number"
                                    value={formData.baseline_year}
                                    onChange={(e) => handleInputChange('baseline_year', parseInt(e.target.value))}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Verification</label>
                                <select
                                    value={formData.baseline_verification}
                                    onChange={(e) => handleInputChange('baseline_verification', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border"
                                >
                                    {VERIFICATION_TYPES.map(v => (
                                        <option key={v.value} value={v.value}>{v.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Optional Fields */}
                    <div className="bg-card rounded-xl p-6 border border-border space-y-4">
                        <h3 className="font-semibold flex items-center gap-2 text-lg">
                            <Building2 className="w-5 h-5 text-primary" />
                            Additional Context (Optional)
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Company Size</label>
                                <select
                                    value={formData.company_size_proxy}
                                    onChange={(e) => handleInputChange('company_size_proxy', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border"
                                >
                                    <option value="">Select size...</option>
                                    <option value="small">Small (&lt;€50M revenue)</option>
                                    <option value="medium">Medium (€50M-€500M)</option>
                                    <option value="large">Large (€500M-€5B)</option>
                                    <option value="enterprise">Enterprise (&gt;€5B)</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Emissions Scope (Carbon)</label>
                                <select
                                    value={formData.emissions_scope}
                                    onChange={(e) => handleInputChange('emissions_scope', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border"
                                >
                                    <option value="">Select scope...</option>
                                    <option value="scope_1_2">Scope 1 + 2</option>
                                    <option value="scope_3">Scope 3</option>
                                    <option value="all">All Scopes</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Methodology</label>
                                <select
                                    value={formData.methodology}
                                    onChange={(e) => handleInputChange('methodology', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border"
                                >
                                    <option value="">Select methodology...</option>
                                    <option value="baseline_year">Baseline Year</option>
                                    <option value="yoy">Year-over-Year</option>
                                    <option value="intensity">Intensity-based</option>
                                    <option value="absolute">Absolute Target</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">CSRD Reporting</label>
                                <select
                                    value={formData.csrd_reporting_status}
                                    onChange={(e) => handleInputChange('csrd_reporting_status', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border"
                                >
                                    <option value="unknown">Unknown</option>
                                    <option value="yes">Yes</option>
                                    <option value="no">No</option>
                                    <option value="in_progress">In Progress</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">CapEx Budget (if known)</label>
                            <input
                                type="text"
                                value={formData.capex_budget}
                                onChange={(e) => handleInputChange('capex_budget', e.target.value)}
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                                placeholder="e.g., €10M sustainability investment"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Implementation Plan Description</label>
                            <textarea
                                value={formData.plan_description}
                                onChange={(e) => handleInputChange('plan_description', e.target.value)}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                                placeholder="Briefly describe how the company plans to achieve this target..."
                            />
                        </div>

                        <button
                            onClick={handleSubmitForm}
                            disabled={!formData.company_name || !formData.industry_sector || !formData.metric || createMutation.isPending}
                            className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                            Continue to Document Upload
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* Step 2: Document Upload */}
            {!showHistory && step === 'documents' && (
                <div className="max-w-2xl mx-auto">
                    <div className="bg-card rounded-xl p-8 border border-border space-y-6">
                        <div className="text-center">
                            <Upload className="w-12 h-12 text-primary mx-auto mb-4" />
                            <h3 className="text-xl font-semibold">Upload Supporting Documents</h3>
                            <p className="text-muted-foreground mt-2">
                                Upload CSRD sustainability statements, ESG reports, or SPO documents for AI verification
                            </p>
                        </div>

                        <div className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary/50 transition-colors">
                            <input
                                type="file"
                                multiple
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="hidden"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer">
                                <FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                                <p className="font-medium">Click to upload PDF documents</p>
                                <p className="text-sm text-muted-foreground mt-1">or drag and drop</p>
                            </label>
                        </div>

                        {uploadedFiles.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm font-medium">Selected Files:</p>
                                {uploadedFiles.map((file, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm bg-muted rounded-lg px-3 py-2">
                                        <FileCheck className="w-4 h-4 text-green-500" />
                                        {file.name}
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="flex gap-4">
                            <button
                                onClick={handleSubmitDocuments}
                                disabled={attachDocsMutation.isPending || runMutation.isPending}
                                className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {(attachDocsMutation.isPending || runMutation.isPending) && <Loader2 className="w-4 h-4 animate-spin" />}
                                {uploadedFiles.length > 0 ? 'Upload & Run Verification' : 'Skip & Run Verification'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Step 3: Running */}
            {!showHistory && step === 'running' && (
                <div className="max-w-xl mx-auto text-center py-12">
                    <div className="bg-card rounded-xl p-12 border border-border">
                        <Loader2 className="w-16 h-16 text-primary mx-auto mb-6 animate-spin" />
                        <h3 className="text-xl font-semibold mb-2">AI Verification in Progress</h3>
                        <p className="text-muted-foreground">
                            Analyzing target against industry benchmarks, extracting evidence from documents, and generating assessment...
                        </p>
                        <div className="mt-6 space-y-2 text-sm text-left max-w-sm mx-auto">
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <CheckCircle2 className="w-4 h-4 text-green-500" /> Input validation complete
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Loader2 className="w-4 h-4 animate-spin" /> Extracting document evidence...
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground opacity-50">
                                <div className="w-4 h-4" /> Searching industry benchmarks
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground opacity-50">
                                <div className="w-4 h-4" /> Computing assessment score
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Step 4: Results */}
            {!showHistory && step === 'result' && (
                <div className="space-y-6">
                    {isLoadingResult ? (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto" />
                        </div>
                    ) : evaluationResult?.data ? (
                        <>
                            {/* Assessment Header */}
                            <div className="bg-card rounded-xl p-6 border border-border">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-semibold">{evaluationResult.data.company_name}</h3>
                                        <p className="text-muted-foreground">{evaluationResult.data.metric?.replace(/_/g, ' ')}</p>
                                    </div>
                                    <div className={`px-6 py-3 rounded-xl text-xl font-bold ${getGradeColor(evaluationResult.data.assessment_grade)}`}>
                                        {evaluationResult.data.assessment_grade || 'PENDING'}
                                    </div>
                                </div>
                            </div>

                            {/* Results Grid */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="bg-card rounded-xl p-6 border border-border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Scale className="w-5 h-5 text-primary" />
                                        <span className="font-medium">Success Probability</span>
                                    </div>
                                    <p className="text-3xl font-bold">
                                        {((evaluationResult.data.success_probability || 0) * 100).toFixed(0)}%
                                    </p>
                                </div>
                                <div className="bg-card rounded-xl p-6 border border-border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Target className="w-5 h-5 text-primary" />
                                        <span className="font-medium">Status</span>
                                    </div>
                                    <p className="text-lg font-semibold capitalize">{evaluationResult.data.status}</p>
                                </div>
                                <div className="bg-card rounded-xl p-6 border border-border">
                                    <div className="flex items-center gap-2 mb-2">
                                        {evaluationResult.data.needs_review ? (
                                            <AlertTriangle className="w-5 h-5 text-yellow-500" />
                                        ) : (
                                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                                        )}
                                        <span className="font-medium">Review Status</span>
                                    </div>
                                    <p className="text-lg font-semibold">
                                        {evaluationResult.data.needs_review ? 'Needs Review' : 'Ready for Decision'}
                                    </p>
                                </div>
                            </div>

                            {/* Summary */}
                            {evaluationResult.data.result_summary && (
                                <div className="bg-card rounded-xl p-6 border border-border">
                                    <h4 className="font-semibold mb-3 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-primary" />
                                        AI Assessment Summary
                                    </h4>
                                    <p className="text-muted-foreground">{evaluationResult.data.result_summary}</p>
                                </div>
                            )}

                            {/* Banker Decision */}
                            {evaluationResult.data.banker_decision === 'PENDING' && (
                                <div className="bg-card rounded-xl p-6 border border-border">
                                    <h4 className="font-semibold mb-4">Submit Your Decision</h4>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => handleDecision('ACCEPT_AS_IS')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                                        >
                                            <CheckCircle2 className="w-5 h-5" /> Accept
                                        </button>
                                        <button
                                            onClick={() => handleDecision('NEGOTIATE')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-yellow-600 text-white rounded-lg font-medium hover:bg-yellow-700 transition-colors flex items-center justify-center gap-2"
                                        >
                                            <AlertTriangle className="w-5 h-5" /> Negotiate
                                        </button>
                                        <button
                                            onClick={() => handleDecision('REJECT')}
                                            disabled={decisionMutation.isPending}
                                            className="flex-1 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                                        >
                                            <XCircle className="w-5 h-5" /> Reject
                                        </button>
                                    </div>
                                </div>
                            )}

                            {evaluationResult.data.banker_decision !== 'PENDING' && (
                                <div className="bg-card rounded-xl p-6 border border-green-500/30 bg-green-500/5">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                                        <span className="font-semibold">Decision Recorded: {evaluationResult.data.banker_decision}</span>
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-12 text-muted-foreground">
                            No evaluation data found.
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
