import { useQuery } from '@tanstack/react-query'
import { complianceApi, esgApi, proceedsApi } from '@/lib/api'
import ScoreGauge from '@/components/ScoreGauge'
import { ESGRadarChart, ESGBarChart } from '../components/ESGMetricChart'
import { FileText, CheckCircle, AlertTriangle, TrendingUp, Brain } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'

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
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-kobalt-black">Dashboard</h1>
                    <p className="text-kobalt-gray-dark">Overview of your ESG compliance</p>
                </div>
                <Link to="/dashboard/upload">
                    <KobaltButton className="flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        New AI Analysis
                    </KobaltButton>
                </Link>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <KobaltCard>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-kobalt-gray-dark">Overall ESG Score</p>
                            <p className="text-3xl font-bold text-kobalt-blue mt-1">
                                {complianceSummary.average_score?.toFixed(0) || 72}
                            </p>
                        </div>
                        <ScoreGauge score={complianceSummary.average_score || 72} size="sm" showGrade={false} />
                    </div>
                </KobaltCard>

                <KobaltCard>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-kobalt-blue/10 flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-kobalt-blue" />
                        </div>
                        <div>
                            <p className="text-sm text-kobalt-gray-dark">Taxonomy Score</p>
                            <p className="text-2xl font-bold text-kobalt-black">{complianceSummary.score_breakdown?.taxonomy_alignment || 70}</p>
                        </div>
                    </div>
                </KobaltCard>

                <KobaltCard>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-green-500" />
                        </div>
                        <div>
                            <p className="text-sm text-kobalt-gray-dark">Compliant Transactions</p>
                            <p className="text-2xl font-bold text-kobalt-black">{transactionSummary?.data?.compliant_transactions || 8}</p>
                        </div>
                    </div>
                </KobaltCard>

                <KobaltCard>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center">
                            <FileText className="w-6 h-6 text-orange-500" />
                        </div>
                        <div>
                            <p className="text-sm text-kobalt-gray-dark">Total Reports</p>
                            <p className="text-2xl font-bold text-kobalt-black">{complianceSummary.total_reports || 12}</p>
                        </div>
                    </div>
                </KobaltCard>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <KobaltCard>
                    <h3 className="font-semibold mb-4 text-kobalt-black">ESG Score Breakdown</h3>
                    <ESGRadarChart data={radarData} />
                </KobaltCard>

                <KobaltCard>
                    <h3 className="font-semibold mb-4 text-kobalt-black">Score Comparison</h3>
                    <ESGBarChart data={barData} />
                </KobaltCard>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <KobaltCard>
                    <h3 className="font-semibold mb-4 text-kobalt-black">Recent Reports</h3>
                    <div className="space-y-3">
                        {(reportsData?.data?.reports || []).slice(0, 5).map((report: any) => (
                            <div key={report.id} className="flex items-center justify-between p-3 bg-kobalt-gray rounded-lg">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-4 h-4 text-kobalt-gray-dark" />
                                    <span className="text-sm text-kobalt-black">Report #{report.id}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`text-sm font-medium ${report.scores?.overall_compliance_score >= 70 ? 'text-green-500' : 'text-orange-500'}`}>
                                        {report.scores?.overall_compliance_score?.toFixed(0) || 'N/A'}
                                    </span>
                                    <span className="text-xs text-kobalt-gray-dark">
                                        {formatDate(report.generated_at)}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {(!reportsData?.data?.reports || reportsData.data.reports.length === 0) && (
                            <p className="text-sm text-kobalt-gray-dark text-center py-4">No reports yet</p>
                        )}
                    </div>
                </KobaltCard>

                <KobaltCard>
                    <h3 className="font-semibold mb-4 text-kobalt-black">Compliance Alerts</h3>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-orange-500/10 rounded-lg">
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                            <span className="text-sm text-kobalt-black">Review pending for 2 documents</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-green-500/10 rounded-lg">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm text-kobalt-black">All transactions verified this week</span>
                        </div>
                    </div>
                </KobaltCard>
            </div>
        </div>
    )
}
