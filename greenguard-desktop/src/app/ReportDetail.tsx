import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { complianceApi, esgApi, aiEsgApi } from '@/lib/api'
import ScoreGauge from '@/components/ScoreGauge'
import { ESGRadarChart, ESGBarChart } from '@/components/ESGMetricChart'
import { ArrowLeft, Loader2, AlertTriangle, ChevronDown, ChevronUp, MessageSquare, Send, Sparkles, Brain } from 'lucide-react'
import { useState } from 'react'

interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
}

export default function ReportDetail() {
    const { id } = useParams()
    const [showRawText, setShowRawText] = useState(false)
    const [showQA, setShowQA] = useState(false)
    const [question, setQuestion] = useState('')
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])

    const { data: scoreData, isLoading: loadingScore } = useQuery({
        queryKey: ['compliance-score', id],
        queryFn: () => complianceApi.getScore(Number(id)),
        enabled: !!id,
    })

    const { data: reportData, isLoading: loadingReport } = useQuery({
        queryKey: ['esg-report', id],
        queryFn: () => esgApi.getReport(Number(id)),
        enabled: !!id,
    })

    const askMutation = useMutation({
        mutationFn: (q: string) => aiEsgApi.askDocument(Number(reportData?.data?.document_id), q),
        onSuccess: (response) => {
            setChatHistory(prev => [...prev, { role: 'assistant', content: response.data.answer }])
        },
        onError: () => {
            setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I could not process your question. Please try again.' }])
        },
    })

    const handleAskQuestion = () => {
        if (!question.trim() || askMutation.isPending) return
        setChatHistory(prev => [...prev, { role: 'user', content: question }])
        askMutation.mutate(question)
        setQuestion('')
    }

    const isLoading = loadingScore || loadingReport
    const score = scoreData?.data || {}
    const report = reportData?.data || {}

    // Get AI analysis data from raw_metrics if available
    const aiAnalysis = report.raw_metrics || {}
    const hasAIAnalysis = aiAnalysis.themes || aiAnalysis.taxonomy_alignment

    const radarData = [
        { subject: 'Carbon', score: score.carbon_score || report.scores?.carbon_score || 0, fullMark: 100 },
        { subject: 'Energy', score: score.energy_efficiency_score || report.scores?.energy_efficiency_score || 0, fullMark: 100 },
        { subject: 'Taxonomy', score: score.taxonomy_alignment_score || report.scores?.taxonomy_alignment_score || 0, fullMark: 100 },
        { subject: 'Social', score: aiAnalysis.scores?.social_score || 65, fullMark: 100 },
        { subject: 'Governance', score: aiAnalysis.scores?.governance_score || 70, fullMark: 100 },
    ]

    const barData = [
        { name: 'Carbon', value: score.carbon_score || 0, benchmark: 70 },
        { name: 'Energy', value: score.energy_efficiency_score || 0, benchmark: 75 },
        { name: 'Taxonomy', value: score.taxonomy_alignment_score || 0, benchmark: 65 },
    ]

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-4">
                <Link to="/reports" className="p-2 hover:bg-muted rounded-lg transition-colors">
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        Report #{id}
                        {hasAIAnalysis && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full flex items-center gap-1">
                                <Brain className="w-3 h-3" /> AI Analyzed
                            </span>
                        )}
                    </h1>
                    <p className="text-muted-foreground">Detailed ESG compliance analysis</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Overall Score */}
                <div className="bg-card rounded-xl p-6 border border-border flex flex-col items-center">
                    <ScoreGauge score={score.overall_score || report.scores?.overall_compliance_score || 0} size="lg" label="Overall Compliance" />
                    <div className="mt-4 text-center">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${score.status === 'Compliant' ? 'bg-green-500/10 text-green-500' :
                            score.status === 'Partially Compliant' ? 'bg-yellow-500/10 text-yellow-500' :
                                'bg-red-500/10 text-red-500'
                            }`}>
                            {score.status || 'Pending'}
                        </span>
                    </div>
                </div>

                {/* Score Breakdown */}
                <div className="lg:col-span-2 bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Score Breakdown</h3>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-muted rounded-lg">
                            <ScoreGauge score={score.carbon_score || 0} size="sm" showGrade={false} />
                            <p className="text-sm font-medium mt-2">Carbon</p>
                        </div>
                        <div className="text-center p-4 bg-muted rounded-lg">
                            <ScoreGauge score={score.energy_efficiency_score || 0} size="sm" showGrade={false} />
                            <p className="text-sm font-medium mt-2">Energy</p>
                        </div>
                        <div className="text-center p-4 bg-muted rounded-lg">
                            <ScoreGauge score={score.taxonomy_alignment_score || 0} size="sm" showGrade={false} />
                            <p className="text-sm font-medium mt-2">Taxonomy</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* AI Summary */}
            {aiAnalysis.summary && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary" />
                        AI Summary
                    </h3>
                    <p className="text-muted-foreground">{aiAnalysis.summary}</p>
                </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">ESG Radar</h3>
                    <ESGRadarChart data={radarData} />
                </div>
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Benchmark Comparison</h3>
                    <ESGBarChart data={barData} />
                </div>
            </div>

            {/* Taxonomy Alignment */}
            {aiAnalysis.taxonomy_alignment && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">EU Taxonomy Alignment</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-muted rounded-lg text-center">
                            <p className="text-3xl font-bold text-primary">
                                {aiAnalysis.taxonomy_alignment.alignment_score || 0}%
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">Alignment Score</p>
                        </div>
                        <div className="md:col-span-2 p-4 bg-muted rounded-lg">
                            <p className="text-sm font-medium mb-2">Assessment</p>
                            <p className="text-sm text-muted-foreground">
                                {aiAnalysis.taxonomy_alignment.assessment || 'No assessment available'}
                            </p>
                        </div>
                    </div>
                    {aiAnalysis.taxonomy_alignment.eligible_activities?.length > 0 && (
                        <div className="mt-4">
                            <p className="text-sm font-medium mb-2">Eligible Activities</p>
                            <div className="flex flex-wrap gap-2">
                                {aiAnalysis.taxonomy_alignment.eligible_activities.map((activity: string, i: number) => (
                                    <span key={i} className="px-3 py-1 bg-green-500/10 text-green-500 text-xs rounded-full">
                                        {activity}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Red Flags */}
            {(score.breakdown?.red_flags?.length > 0 || aiAnalysis.red_flags?.length > 0) && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-orange-500" />
                        Red Flags Detected
                    </h3>
                    <div className="space-y-2">
                        {(aiAnalysis.red_flags || score.breakdown?.red_flags || []).map((flag: any, i: number) => (
                            <div key={i} className={`p-3 rounded-lg ${flag.severity === 'high' ? 'bg-red-500/10' :
                                flag.severity === 'medium' ? 'bg-orange-500/10' : 'bg-yellow-500/10'
                                }`}>
                                <p className="text-sm font-medium">{flag.issue || flag}</p>
                                {flag.recommendation && (
                                    <p className="text-xs text-muted-foreground mt-1">{flag.recommendation}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendations */}
            {(score.recommendations?.length > 0 || aiAnalysis.recommendations?.length > 0) && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Recommendations</h3>
                    <ul className="space-y-2">
                        {(aiAnalysis.recommendations || score.recommendations || []).map((rec: string, i: number) => (
                            <li key={i} className="flex items-start gap-3 text-sm">
                                <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 text-xs font-medium">
                                    {i + 1}
                                </span>
                                <span className="text-muted-foreground">{rec}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Document Q&A */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">
                <button
                    onClick={() => setShowQA(!showQA)}
                    className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors"
                >
                    <span className="font-semibold flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-primary" />
                        Ask Questions About This Report
                    </span>
                    {showQA ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
                {showQA && (
                    <div className="p-4 border-t border-border">
                        <p className="text-sm text-muted-foreground mb-4">
                            Use AI to ask questions about the document content
                        </p>

                        {/* Chat History */}
                        {chatHistory.length > 0 && (
                            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                                {chatHistory.map((msg, i) => (
                                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.role === 'user'
                                            ? 'bg-primary text-primary-foreground'
                                            : 'bg-muted'
                                            }`}>
                                            {msg.content}
                                        </div>
                                    </div>
                                ))}
                                {askMutation.isPending && (
                                    <div className="flex justify-start">
                                        <div className="bg-muted p-3 rounded-lg">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Question Input */}
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                                placeholder="e.g., What are the main carbon reduction initiatives?"
                                className="flex-1 px-4 py-2 bg-muted rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                            <button
                                onClick={handleAskQuestion}
                                disabled={!question.trim() || askMutation.isPending}
                                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Raw Text (Collapsible) */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">
                <button
                    onClick={() => setShowRawText(!showRawText)}
                    className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors"
                >
                    <span className="font-semibold">Extracted Text</span>
                    {showRawText ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
                {showRawText && (
                    <div className="p-4 border-t border-border max-h-64 overflow-y-auto">
                        <pre className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {report.extracted_text || 'No extracted text available'}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    )
}
