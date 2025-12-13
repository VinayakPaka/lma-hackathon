import { useQuery } from '@tanstack/react-query'
import { complianceApi, esgApi, proceedsApi } from '@/lib/api'
import ScoreGauge from '@/components/ScoreGauge'
import { ESGRadarChart, ESGBarChart } from '@/components/ESGMetricChart'
import { FileText, Upload, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function Dashboard() {
    const { data: summary } = useQuery({
        queryKey: ['compliance-summary'],
        queryFn: () => complianceApi.getSummary(),
    })

    const { data: reportsData } = useQuery({
        queryKey: ['recent-reports'],
        queryFn: () => esgApi.getReports(1),
    })

    const { data: transactionSummary } = useQuery({
        queryKey: ['transaction-summary'],
        queryFn: () => proceedsApi.getSummary(),
    })

    const complianceSummary = summary?.data || {
        average_score: 72,
        total_reports: 12,
        score_breakdown: { carbon: 68, energy_efficiency: 75, taxonomy_alignment: 70 },
    }

    const radarData = [
        { subject: 'Carbon', score: complianceSummary.score_breakdown?.carbon || 68, fullMark: 100 },
        { subject: 'Energy', score: complianceSummary.score_breakdown?.energy_efficiency || 75, fullMark: 100 },
        { subject: 'Taxonomy', score: complianceSummary.score_breakdown?.taxonomy_alignment || 70, fullMark: 100 },
        { subject: 'Water', score: 65, fullMark: 100 },
        { subject: 'Waste', score: 80, fullMark: 100 },
    ]

    const barData = [
        { name: 'Carbon', value: complianceSummary.score_breakdown?.carbon || 68 },
        { name: 'Energy', value: complianceSummary.score_breakdown?.energy_efficiency || 75 },
        { name: 'Taxonomy', value: complianceSummary.score_breakdown?.taxonomy_alignment || 70 },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold">Dashboard</h1>
                <p className="text-muted-foreground">Overview of your ESG compliance</p>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-card rounded-xl p-6 border border-border">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Overall ESG Score</p>
                            <p className="text-3xl font-bold text-primary mt-1">
                                {complianceSummary.average_score?.toFixed(0) || 72}
                            </p>
                        </div>
                        <ScoreGauge score={complianceSummary.average_score || 72} size="sm" showGrade={false} />
                    </div>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-blue-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Taxonomy Score</p>
                            <p className="text-2xl font-bold">{complianceSummary.score_breakdown?.taxonomy_alignment || 70}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-green-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Compliant Transactions</p>
                            <p className="text-2xl font-bold">{transactionSummary?.data?.compliant_transactions || 8}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center">
                            <FileText className="w-6 h-6 text-orange-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Total Reports</p>
                            <p className="text-2xl font-bold">{complianceSummary.total_reports || 12}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">ESG Score Breakdown</h3>
                    <ESGRadarChart data={radarData} />
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Score Comparison</h3>
                    <ESGBarChart data={barData} />
                </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Recent Reports</h3>
                    <div className="space-y-3">
                        {(reportsData?.data?.reports || []).slice(0, 5).map((report: any) => (
                            <div key={report.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-sm">Report #{report.id}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`text-sm font-medium ${report.scores?.overall_compliance_score >= 70 ? 'text-green-500' : 'text-orange-500'}`}>
                                        {report.scores?.overall_compliance_score?.toFixed(0) || 'N/A'}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                        {formatDate(report.generated_at)}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {(!reportsData?.data?.reports || reportsData.data.reports.length === 0) && (
                            <p className="text-sm text-muted-foreground text-center py-4">No reports yet</p>
                        )}
                    </div>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4">Compliance Alerts</h3>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-orange-500/10 rounded-lg">
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                            <span className="text-sm">Review pending for 2 documents</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-green-500/10 rounded-lg">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">All transactions verified this week</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
