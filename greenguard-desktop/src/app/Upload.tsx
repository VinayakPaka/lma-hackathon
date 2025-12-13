import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { uploadApi, esgApi } from '@/lib/api'
import FilePicker from '@/components/FilePicker'
import { CheckCircle, FileText, Loader2, Sparkles } from 'lucide-react'

export default function Upload() {
    const [step, setStep] = useState<'upload' | 'extracting' | 'preview' | 'complete'>('upload')
    const [documentId, setDocumentId] = useState<number | null>(null)
    const [extractedData, setExtractedData] = useState<any>(null)

    const uploadMutation = useMutation({
        mutationFn: (file: File) => uploadApi.uploadDocument(file),
        onSuccess: (response) => {
            setDocumentId(response.data.id)
            setStep('extracting')
            extractMutation.mutate(response.data.id)
        },
    })

    const extractMutation = useMutation({
        mutationFn: (docId: number) => esgApi.extractESG(docId),
        onSuccess: (response) => {
            setExtractedData(response.data)
            setStep('preview')
        },
        onError: () => {
            setStep('preview')
            setExtractedData({ error: 'Extraction failed. Please try again.' })
        },
    })

    const handleFileSelect = (file: File) => {
        uploadMutation.mutate(file)
    }

    const handleGenerateReport = () => {
        setStep('complete')
    }

    const handleReset = () => {
        setStep('upload')
        setDocumentId(null)
        setExtractedData(null)
    }

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold">Upload Document</h1>
                <p className="text-muted-foreground">Upload PDF or image files for ESG analysis</p>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center gap-4">
                {['Upload', 'Extract', 'Preview', 'Complete'].map((label, index) => {
                    const stepIndex = ['upload', 'extracting', 'preview', 'complete'].indexOf(step)
                    const isActive = index <= stepIndex
                    return (
                        <div key={label} className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                                }`}>
                                {index + 1}
                            </div>
                            <span className={`text-sm ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                                {label}
                            </span>
                            {index < 3 && <div className="w-8 h-px bg-border" />}
                        </div>
                    )
                })}
            </div>

            {/* Step Content */}
            <div className="bg-card rounded-xl p-6 border border-border">
                {step === 'upload' && (
                    <FilePicker onFileSelect={handleFileSelect} isUploading={uploadMutation.isPending} />
                )}

                {step === 'extracting' && (
                    <div className="text-center py-12">
                        <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
                        <p className="text-lg font-medium">Extracting ESG Data...</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Analyzing document #{documentId} for environmental metrics
                        </p>
                    </div>
                )}

                {step === 'preview' && extractedData && (
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <Sparkles className="w-6 h-6 text-primary" />
                            <h3 className="text-lg font-semibold">Extraction Preview</h3>
                        </div>

                        {extractedData.error ? (
                            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
                                {extractedData.error}
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-muted rounded-lg">
                                        <p className="text-sm text-muted-foreground">Carbon Score</p>
                                        <p className="text-2xl font-bold text-primary">
                                            {extractedData.scores?.carbon_score?.toFixed(1) || 'N/A'}
                                        </p>
                                    </div>
                                    <div className="p-4 bg-muted rounded-lg">
                                        <p className="text-sm text-muted-foreground">Energy Score</p>
                                        <p className="text-2xl font-bold text-primary">
                                            {extractedData.scores?.energy_efficiency_score?.toFixed(1) || 'N/A'}
                                        </p>
                                    </div>
                                </div>

                                {extractedData.detected_keywords?.length > 0 && (
                                    <div>
                                        <p className="text-sm font-medium mb-2">Detected Keywords</p>
                                        <div className="flex flex-wrap gap-2">
                                            {extractedData.detected_keywords.slice(0, 10).map((kw: string, i: number) => (
                                                <span key={i} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                                                    {kw}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={handleGenerateReport}
                                    className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                                >
                                    Generate ESG Report
                                </button>
                            </>
                        )}
                    </div>
                )}

                {step === 'complete' && (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                            <CheckCircle className="w-10 h-10 text-green-500" />
                        </div>
                        <p className="text-lg font-medium">ESG Report Generated!</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Your report is ready to view
                        </p>
                        <div className="flex gap-3 justify-center mt-6">
                            <button
                                onClick={() => window.location.href = `/reports/${documentId}`}
                                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                            >
                                View Report
                            </button>
                            <button
                                onClick={handleReset}
                                className="px-6 py-2 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
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
