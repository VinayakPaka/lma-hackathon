import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { uploadApi, aiEsgApi } from '@/lib/api'
import FilePicker from '@/components/FilePicker'
import { CheckCircle, FileText, Loader2, Sparkles, Brain, Zap, AlertTriangle } from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'

type UploadStep = 'upload' | 'processing' | 'analyzing' | 'preview' | 'complete'

interface AIAnalysisResult {
    report_id: number
    document_id: number
    analysis_type: string
    metrics: Record<string, any>
    scores: Record<string, number>
    keywords: Record<string, string[]>
    themes: string[]
    red_flags: Array<{ issue: string; severity: string; recommendation: string }>
    taxonomy_alignment: { eligible_activities: string[]; alignment_score: number; assessment: string }
    summary: string
    recommendations: string[]
}

export default function Upload() {
    const [step, setStep] = useState<UploadStep>('upload')
    const [documentId, setDocumentId] = useState<number | null>(null)
    const [extractedData, setExtractedData] = useState<AIAnalysisResult | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [processingMessage, setProcessingMessage] = useState('')

    // Poll for document processing status
    const { data: documentData } = useQuery({
        queryKey: ['document-status', documentId],
        queryFn: () => uploadApi.getDocument(documentId!),
        enabled: !!documentId && step === 'processing',
        refetchInterval: 2000, // Poll every 2 seconds
    })

    // Check if document processing is complete
    useEffect(() => {
        if (documentData?.data?.extraction_status === 'completed' && step === 'processing') {
            setStep('analyzing')
            setProcessingMessage('Running AI-powered ESG analysis...')
            aiAnalysisMutation.mutate(documentId!)
        } else if (documentData?.data?.extraction_status === 'failed') {
            setError('Document text extraction failed. Please try a different file.')
            setStep('upload')
        }
    }, [documentData?.data?.extraction_status])

    const uploadMutation = useMutation({
        mutationFn: (file: File) => uploadApi.uploadDocument(file),
        onSuccess: (response) => {
            setDocumentId(response.data.id)
            setStep('processing')
            setProcessingMessage('Extracting text and generating embeddings...')
            setError(null)
        },
        onError: (err: any) => {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.')
        },
    })

    const aiAnalysisMutation = useMutation({
        mutationFn: (docId: number) => aiEsgApi.extractWithAI(docId),
        onSuccess: (response) => {
            setExtractedData(response.data)
            setStep('preview')
        },
        onError: (err: any) => {
            setError(err.response?.data?.detail || 'AI analysis failed. Please try again.')
            setStep('upload')
        },
    })

    const handleFileSelect = (file: File) => {
        setError(null)
        uploadMutation.mutate(file)
    }

    const handleGenerateReport = () => {
        setStep('complete')
    }

    const handleReset = () => {
        setStep('upload')
        setDocumentId(null)
        setExtractedData(null)
        setError(null)
    }

    const getScoreColor = (score: number) => {
        if (score >= 75) return 'text-green-600'
        if (score >= 50) return 'text-yellow-600'
        return 'text-red-600'
    }

    const getSeverityColor = (severity: string) => {
        if (severity === 'high') return 'bg-red-50 text-red-700 border-red-100'
        if (severity === 'medium') return 'bg-yellow-50 text-yellow-700 border-yellow-100'
        return 'bg-blue-50 text-blue-700 border-blue-100'
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-12">
            <div>
                <h1 className="text-3xl font-bold text-kobalt-black flex items-center gap-3">
                    <div className="p-2 bg-kobalt-blue/10 rounded-xl">
                        <Brain className="w-8 h-8 text-kobalt-blue" />
                    </div>
                    AI-Powered ESG Analysis
                </h1>
                <p className="text-kobalt-gray-dark mt-2 text-lg">Upload documents for intelligent ESG analysis using AI</p>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center gap-2 sm:gap-4">
                {[
                    { key: 'upload', label: 'Upload', icon: FileText },
                    { key: 'processing', label: 'Process', icon: Loader2 },
                    { key: 'analyzing', label: 'AI Analysis', icon: Brain },
                    { key: 'preview', label: 'Preview', icon: Sparkles },
                    { key: 'complete', label: 'Complete', icon: CheckCircle },
                ].map((s, index) => {
                    const steps: UploadStep[] = ['upload', 'processing', 'analyzing', 'preview', 'complete']
                    const stepIndex = steps.indexOf(step)
                    const isActive = index <= stepIndex
                    const isCurrent = steps[index] === step
                    const Icon = s.icon
                    return (
                        <div key={s.key} className="flex items-center gap-2">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${isCurrent ? 'bg-kobalt-blue text-white shadow-lg shadow-kobalt-blue/20 scale-110' :
                                isActive ? 'bg-kobalt-blue/10 text-kobalt-blue' : 'bg-white border border-[#E5E5E5] text-kobalt-gray-dark'
                                }`}>
                                <Icon className={`w-5 h-5 ${isCurrent && (step === 'processing' || step === 'analyzing') ? 'animate-spin' : ''}`} />
                            </div>
                            <span className={`text-sm hidden sm:inline transition-colors duration-200 ${isActive ? 'text-kobalt-black font-semibold' : 'text-kobalt-gray-dark'}`}>
                                {s.label}
                            </span>
                            {index < 4 && <div className={`w-4 sm:w-12 h-0.5 transition-colors duration-300 ${isActive ? 'bg-kobalt-blue' : 'bg-[#E5E5E5]'}`} />}
                        </div>
                    )
                })}
            </div>

            {/* Error Display */}
            {error && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 flex items-center gap-3 shadow-sm">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <span className="font-medium">{error}</span>
                </div>
            )}

            {/* Step Content */}
            <KobaltCard padding="lg" className="min-h-[400px]">
                {step === 'upload' && (
                    <FilePicker onFileSelect={handleFileSelect} isUploading={uploadMutation.isPending} />
                )}

                {(step === 'processing' || step === 'analyzing') && (
                    <div className="text-center py-20">
                        <div className="relative w-24 h-24 mx-auto mb-8">
                            <div className="absolute inset-0 rounded-full border-4 border-kobalt-blue/10"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-kobalt-blue border-t-transparent animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                {step === 'processing' ? (
                                    <Zap className="w-10 h-10 text-kobalt-blue" />
                                ) : (
                                    <Brain className="w-10 h-10 text-kobalt-blue" />
                                )}
                            </div>
                        </div>
                        <h3 className="text-xl font-bold text-kobalt-black mb-2">
                            {step === 'processing' ? 'Processing Document...' : 'AI Analysis in Progress...'}
                        </h3>
                        <p className="text-kobalt-gray-dark">
                            {processingMessage}
                        </p>
                        {step === 'analyzing' && (
                            <div className="mt-6 flex justify-center gap-3">
                                <span className="px-4 py-1.5 bg-kobalt-blue/5 text-kobalt-blue text-xs font-semibold rounded-full border border-kobalt-blue/10">
                                    Perplexity AI
                                </span>
                                <span className="px-4 py-1.5 bg-kobalt-blue/5 text-kobalt-blue text-xs font-semibold rounded-full border border-kobalt-blue/10">
                                    RAG Enabled
                                </span>
                            </div>
                        )}
                    </div>
                )}

                {step === 'preview' && extractedData && (
                    <div className="space-y-8">
                        <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-kobalt-blue/10 rounded-xl">
                                    <Sparkles className="w-6 h-6 text-kobalt-blue" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-kobalt-black">AI Analysis Complete</h3>
                                    <p className="text-sm text-kobalt-gray-dark">
                                        Analyzed with {extractedData.analysis_type === 'ai_powered' ? 'Perplexity AI' : 'Regex Fallback'}
                                    </p>
                                </div>
                            </div>
                            <div className={`px-4 py-2 rounded-xl text-lg font-bold border ${extractedData.scores?.overall_compliance_score >= 50 ? 'bg-green-50 text-green-700 border-green-100' : 'bg-red-50 text-red-700 border-red-100'}`}>
                                Score: {extractedData.scores?.overall_compliance_score?.toFixed(1) || 'N/A'}
                            </div>
                        </div>

                        {/* Summary */}
                        {extractedData.summary && (
                            <div className="p-6 bg-[#F7F7F5] rounded-xl border border-[#E5E5E5]">
                                <h4 className="text-sm font-bold text-kobalt-black uppercase tracking-wider mb-2">Executive Summary</h4>
                                <p className="text-kobalt-gray-dark leading-relaxed">{extractedData.summary}</p>
                            </div>
                        )}

                        {/* Score Cards */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {[
                                { label: 'Carbon Score', value: extractedData.scores?.carbon_score },
                                { label: 'Energy Score', value: extractedData.scores?.energy_efficiency_score },
                                { label: 'Taxonomy Score', value: extractedData.scores?.taxonomy_alignment_score },
                                { label: 'Overall Score', value: extractedData.scores?.overall_compliance_score },
                            ].map((score) => (
                                <div key={score.label} className="p-5 bg-white rounded-xl border border-[#E5E5E5] text-center hover:shadow-md transition-shadow">
                                    <p className="text-xs font-bold text-kobalt-gray-dark uppercase mb-2">{score.label}</p>
                                    <p className={`text-3xl font-bold ${getScoreColor(score.value || 0)}`}>
                                        {score.value?.toFixed(1) || 'N/A'}
                                    </p>
                                </div>
                            ))}
                        </div>

                        {/* Themes */}
                        {extractedData.themes?.length > 0 && (
                            <div>
                                <p className="text-sm font-bold text-kobalt-black uppercase mb-3">ESG Themes Identified</p>
                                <div className="flex flex-wrap gap-2">
                                    {extractedData.themes.map((theme, i) => (
                                        <span key={i} className="px-3 py-1.5 bg-kobalt-blue/5 text-kobalt-blue text-sm font-medium rounded-lg border border-kobalt-blue/10">
                                            {theme}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Red Flags */}
                        {extractedData.red_flags?.length > 0 && (
                            <div>
                                <p className="text-sm font-bold text-kobalt-black uppercase mb-3 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                                    Red Flags Detected ({extractedData.red_flags.length})
                                </p>
                                <div className="space-y-3">
                                    {extractedData.red_flags.slice(0, 3).map((flag, i) => (
                                        <div key={i} className={`p-4 rounded-xl border ${getSeverityColor(flag.severity)}`}>
                                            <p className="font-bold text-sm mb-1">{flag.issue}</p>
                                            {flag.recommendation && (
                                                <p className="text-sm opacity-90">{flag.recommendation}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recommendations */}
                        {extractedData.recommendations?.length > 0 && (
                            <div>
                                <p className="text-sm font-bold text-kobalt-black uppercase mb-3">AI Recommendations</p>
                                <ul className="space-y-2">
                                    {extractedData.recommendations.slice(0, 4).map((rec, i) => (
                                        <li key={i} className="text-sm text-kobalt-gray-dark flex items-start gap-3 bg-white p-3 rounded-lg border border-[#E5E5E5]">
                                            <span className="text-kobalt-blue font-bold mt-0.5">→</span>
                                            {rec}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <KobaltButton
                            onClick={handleGenerateReport}
                            className="w-full h-12 text-lg"
                        >
                            <CheckCircle className="w-5 h-5 mr-2" />
                            Save ESG Report
                        </KobaltButton>
                    </div>
                )}

                {step === 'complete' && (
                    <div className="text-center py-20">
                        <div className="w-24 h-24 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-6 border-4 border-green-100">
                            <CheckCircle className="w-12 h-12 text-green-600" />
                        </div>
                        <h3 className="text-2xl font-bold text-kobalt-black">ESG Report Generated!</h3>
                        <p className="text-kobalt-gray-dark mt-2 text-lg">
                            Your AI-powered ESG analysis report is ready to view
                        </p>
                        <div className="flex gap-4 justify-center mt-8">
                            <KobaltButton
                                onClick={() => window.location.href = `/reports/${extractedData?.report_id}`}
                                className="min-w-[160px]"
                            >
                                View Report
                            </KobaltButton>
                            <KobaltButton
                                variant="secondary"
                                onClick={handleReset}
                                className="min-w-[160px]"
                            >
                                Upload Another
                            </KobaltButton>
                        </div>
                    </div>
                )}
            </KobaltCard>
        </div>
    )
}
