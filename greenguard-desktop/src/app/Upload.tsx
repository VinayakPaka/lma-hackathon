import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { uploadApi, aiEsgApi } from '@/lib/api'
import FilePicker from '@/components/FilePicker'
import { CheckCircle, FileText, Loader2, Sparkles, Brain, Zap, AlertTriangle } from 'lucide-react'

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
        if (score >= 75) return 'text-green-500'
        if (score >= 50) return 'text-yellow-500'
        return 'text-red-500'
    }

    const getSeverityColor = (severity: string) => {
        if (severity === 'high') return 'bg-red-500/10 text-red-500 border-red-500/20'
        if (severity === 'medium') return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Brain className="w-7 h-7 text-primary" />
                    AI-Powered ESG Analysis
                </h1>
                <p className="text-muted-foreground">Upload documents for intelligent ESG analysis using AI</p>
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
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${isCurrent ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2 ring-offset-background' :
                                isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                                }`}>
                                <Icon className={`w-4 h-4 ${isCurrent && (step === 'processing' || step === 'analyzing') ? 'animate-spin' : ''}`} />
                            </div>
                            <span className={`text-sm hidden sm:inline ${isActive ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                                {s.label}
                            </span>
                            {index < 4 && <div className={`w-4 sm:w-8 h-px ${isActive ? 'bg-primary' : 'bg-border'}`} />}
                        </div>
                    )
                })}
            </div>

            {/* Error Display */}
            {error && (
                <div className="p-4 bg-destructive/10 text-destructive rounded-lg flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {/* Step Content */}
            <div className="bg-card rounded-xl p-6 border border-border">
                {step === 'upload' && (
                    <FilePicker onFileSelect={handleFileSelect} isUploading={uploadMutation.isPending} />
                )}

                {(step === 'processing' || step === 'analyzing') && (
                    <div className="text-center py-12">
                        <div className="relative w-20 h-20 mx-auto mb-6">
                            <div className="absolute inset-0 rounded-full border-4 border-primary/20"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                {step === 'processing' ? (
                                    <Zap className="w-8 h-8 text-primary" />
                                ) : (
                                    <Brain className="w-8 h-8 text-primary" />
                                )}
                            </div>
                        </div>
                        <p className="text-lg font-medium">
                            {step === 'processing' ? 'Processing Document...' : 'AI Analysis in Progress...'}
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                            {processingMessage}
                        </p>
                        {step === 'analyzing' && (
                            <div className="mt-4 flex justify-center gap-2">
                                <span className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">
                                    Perplexity AI
                                </span>
                                <span className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">
                                    RAG Enabled
                                </span>
                            </div>
                        )}
                    </div>
                )}

                {step === 'preview' && extractedData && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-lg">
                                    <Sparkles className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold">AI Analysis Complete</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Analyzed with {extractedData.analysis_type === 'ai_powered' ? 'Perplexity AI' : 'Regex Fallback'}
                                    </p>
                                </div>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(extractedData.scores?.overall_compliance_score || 0)} bg-current/10`}>
                                Score: {extractedData.scores?.overall_compliance_score?.toFixed(1) || 'N/A'}
                            </span>
                        </div>

                        {/* Summary */}
                        {extractedData.summary && (
                            <div className="p-4 bg-muted/50 rounded-lg">
                                <p className="text-sm">{extractedData.summary}</p>
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
                                <div key={score.label} className="p-4 bg-muted rounded-lg text-center">
                                    <p className="text-xs text-muted-foreground mb-1">{score.label}</p>
                                    <p className={`text-2xl font-bold ${getScoreColor(score.value || 0)}`}>
                                        {score.value?.toFixed(1) || 'N/A'}
                                    </p>
                                </div>
                            ))}
                        </div>

                        {/* Themes */}
                        {extractedData.themes?.length > 0 && (
                            <div>
                                <p className="text-sm font-medium mb-2">ESG Themes Identified</p>
                                <div className="flex flex-wrap gap-2">
                                    {extractedData.themes.map((theme, i) => (
                                        <span key={i} className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">
                                            {theme}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Keywords */}
                        {extractedData.keywords && Object.keys(extractedData.keywords).length > 0 && (
                            <div>
                                <p className="text-sm font-medium mb-2">Keywords by Category</p>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {Object.entries(extractedData.keywords).map(([category, words]) => (
                                        <div key={category} className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs font-medium text-muted-foreground capitalize mb-2">{category}</p>
                                            <div className="flex flex-wrap gap-1">
                                                {(words as string[]).slice(0, 5).map((word, i) => (
                                                    <span key={i} className="px-2 py-0.5 bg-background text-xs rounded">
                                                        {word}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Red Flags */}
                        {extractedData.red_flags?.length > 0 && (
                            <div>
                                <p className="text-sm font-medium mb-2 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                                    Red Flags Detected ({extractedData.red_flags.length})
                                </p>
                                <div className="space-y-2">
                                    {extractedData.red_flags.slice(0, 3).map((flag, i) => (
                                        <div key={i} className={`p-3 rounded-lg border ${getSeverityColor(flag.severity)}`}>
                                            <p className="text-sm font-medium">{flag.issue}</p>
                                            {flag.recommendation && (
                                                <p className="text-xs mt-1 opacity-80">{flag.recommendation}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recommendations */}
                        {extractedData.recommendations?.length > 0 && (
                            <div>
                                <p className="text-sm font-medium mb-2">AI Recommendations</p>
                                <ul className="space-y-1">
                                    {extractedData.recommendations.slice(0, 4).map((rec, i) => (
                                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                            <span className="text-primary">→</span>
                                            {rec}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <button
                            onClick={handleGenerateReport}
                            className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                        >
                            <CheckCircle className="w-5 h-5" />
                            Save ESG Report
                        </button>
                    </div>
                )}

                {step === 'complete' && (
                    <div className="text-center py-12">
                        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6">
                            <CheckCircle className="w-12 h-12 text-green-500" />
                        </div>
                        <p className="text-xl font-semibold">ESG Report Generated!</p>
                        <p className="text-sm text-muted-foreground mt-2">
                            Your AI-powered ESG analysis report is ready to view
                        </p>
                        <div className="flex gap-3 justify-center mt-8">
                            <button
                                onClick={() => window.location.href = `/reports/${extractedData?.report_id}`}
                                className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                            >
                                View Report
                            </button>
                            <button
                                onClick={handleReset}
                                className="px-6 py-2.5 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
                            >
                                Upload Another
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
