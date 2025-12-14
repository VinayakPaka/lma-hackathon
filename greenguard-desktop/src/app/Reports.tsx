import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { esgApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { FileText, Eye, Loader2 } from 'lucide-react'

export default function Reports() {
    const { data, isLoading } = useQuery({
        queryKey: ['esg-reports'],
        queryFn: () => esgApi.getReports(1),
    })

    // API returns array directly, not wrapped in { reports: [] }
    const reports = Array.isArray(data?.data) ? data.data : (data?.data?.reports || [])

    const getStatusBadge = (score: number) => {
        if (score >= 75) return { label: 'Compliant', className: 'bg-green-500/10 text-green-500' }
        if (score >= 50) return { label: 'Partial', className: 'bg-yellow-500/10 text-yellow-500' }
        return { label: 'Non-Compliant', className: 'bg-red-500/10 text-red-500' }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">ESG Reports</h1>
                    <p className="text-muted-foreground">View all generated ESG compliance reports</p>
                </div>
                <Link
                    to="/upload"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                >
                    New Report
                </Link>
            </div>

            <div className="bg-card rounded-xl border border-border overflow-hidden">
                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    </div>
                ) : reports.length === 0 ? (
                    <div className="text-center py-12">
                        <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-lg font-medium">No reports yet</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Upload a document to generate your first ESG report
                        </p>
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="text-left px-6 py-3 text-sm font-medium text-muted-foreground">Report ID</th>
                                <th className="text-left px-6 py-3 text-sm font-medium text-muted-foreground">Date</th>
                                <th className="text-left px-6 py-3 text-sm font-medium text-muted-foreground">Overall Score</th>
                                <th className="text-left px-6 py-3 text-sm font-medium text-muted-foreground">Status</th>
                                <th className="text-right px-6 py-3 text-sm font-medium text-muted-foreground">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {reports.map((report: any) => {
                                const score = report.scores?.overall_compliance_score || 0
                                const status = getStatusBadge(score)
                                return (
                                    <tr key={report.id} className="hover:bg-muted/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <FileText className="w-4 h-4 text-muted-foreground" />
                                                <span className="font-medium">#{report.id}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-muted-foreground">
                                            {formatDate(report.generated_at)}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="font-semibold">{score.toFixed(1)}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.className}`}>
                                                {status.label}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <Link
                                                to={`/reports/${report.id}`}
                                                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                                            >
                                                <Eye className="w-4 h-4" />
                                                View
                                            </Link>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
