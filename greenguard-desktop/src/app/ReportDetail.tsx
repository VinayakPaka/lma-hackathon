import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { complianceApi, esgApi } from '@/lib/api'
import ScoreGauge from '@/components/ScoreGauge'
import { ESGRadarChart, ESGBarChart } from '@/components/ESGMetricChart'
import { ArrowLeft, Loader2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function ReportDetail() {
    const { id } = useParams()
    const [showRawText, setShowRawText] = useState(false)

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

    const isLoading = loadingScore || loadingReport
    const score = scoreData?.data || {}
    const report = reportData?.data || {}

    const radarData = [
        { subject: 'Carbon', score: score.carbon_score || 0, fullMark: 100 },
        { subject: 'Energy', score: score.energy_efficiency_score || 0, fullMark: 100 },
        { subject: 'Taxonomy', score: score.taxonomy_alignment_score || 0, fullMark: 100 },
        { subject: 'Water', score: 65, fullMark: 100 },
        { subject: 'Waste', score: 70, fullMark: 100 },
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
                <div>
                    <h1 className="text-2xl font-bold">Report #{id}</h1>
                    <p className="text-muted-foreground">Detailed ESG compliance analysis</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Overall Score */}
                <div className="bg-card rounded-xl p-6 border border-border flex flex-col items-center">
                    <ScoreGauge score={score.overall_score || 0} size="lg" label="Overall Compliance" />
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

            {/* Red Flags */}
            {score.breakdown?.red_flags?.length > 0 && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-orange-500" />
                        Red Flags Detected
                    </h3>
                    <div className="space-y-2">
                        {score.breakdown.red_flags.map((flag: string, i: number) => (
                            <div key={i} className="p-3 bg-orange-500/10 rounded-lg text-sm">
                                {flag}
                            </div>
                        ))}
                    </div>
                </div>
            )}

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
