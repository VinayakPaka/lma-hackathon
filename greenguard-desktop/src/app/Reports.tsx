import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { esgApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { FileText, Eye, Loader2, Plus } from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'

export default function Reports() {
    const { data, isLoading } = useQuery({
        queryKey: ['esg-reports'],
        queryFn: () => esgApi.getReports(1),
    })

    // API returns array directly, not wrapped in { reports: [] }
    const reports = Array.isArray(data?.data) ? data.data : (data?.data?.reports || [])

    const getStatusBadge = (score: number) => {
        if (score >= 75) return { label: 'Compliant', className: 'bg-green-50 text-green-700 border border-green-200' }
        if (score >= 50) return { label: 'Partial', className: 'bg-yellow-50 text-yellow-700 border border-yellow-200' }
        return { label: 'Non-Compliant', className: 'bg-red-50 text-red-700 border border-red-200' }
    }

    return (
        <div className="space-y-6 animate-fade-in pb-12">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-kobalt-black">ESG Reports</h1>
                    <p className="text-kobalt-gray-dark">View all generated ESG compliance reports</p>
                </div>
                <Link to="/dashboard/upload">
                    <KobaltButton className="shadow-lg shadow-kobalt-blue/20">
                        <Plus className="w-4 h-4 mr-2" />
                        New Report
                    </KobaltButton>
                </Link>
            </div>

            <KobaltCard padding="none" className="overflow-hidden">
                {isLoading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 text-kobalt-blue animate-spin" />
                    </div>
                ) : reports.length === 0 ? (
                    <div className="text-center py-20">
                        <div className="w-16 h-16 bg-kobalt-gray/50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <FileText className="w-8 h-8 text-kobalt-gray-dark" />
                        </div>
                        <p className="text-lg font-bold text-kobalt-black">No reports yet</p>
                        <p className="text-sm text-kobalt-gray-dark mt-1">
                            Upload a document to generate your first ESG report
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[#F9F9F8] border-b border-[#E5E5E5]">
                                <tr>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-kobalt-gray-dark uppercase tracking-wider">Report ID</th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-kobalt-gray-dark uppercase tracking-wider">Date</th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-kobalt-gray-dark uppercase tracking-wider">Overall Score</th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-kobalt-gray-dark uppercase tracking-wider">Status</th>
                                    <th className="text-right px-6 py-4 text-xs font-bold text-kobalt-gray-dark uppercase tracking-wider">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#E5E5E5]">
                                {reports.map((report: any) => {
                                    const score = report.scores?.overall_compliance_score || 0
                                    const status = getStatusBadge(score)
                                    return (
                                        <tr key={report.id} className="hover:bg-kobalt-gray/30 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-white border border-[#E5E5E5] rounded-lg group-hover:border-kobalt-blue/30 transition-colors">
                                                        <FileText className="w-4 h-4 text-kobalt-gray-dark group-hover:text-kobalt-blue" />
                                                    </div>
                                                    <span className="font-semibold text-kobalt-black">#{report.id}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-kobalt-black font-medium">
                                                {formatDate(report.generated_at)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-lg font-bold ${score >= 75 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                                                    {score.toFixed(1)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${status.className}`}>
                                                    {status.label}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <Link
                                                    to={`/dashboard/reports/${report.id}`}
                                                    className="inline-flex items-center gap-2 text-sm font-semibold text-kobalt-blue hover:text-blue-700 transition-colors bg-kobalt-blue/5 hover:bg-kobalt-blue/10 px-3 py-1.5 rounded-lg"
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
                    </div>
                )}
            </KobaltCard>
        </div>
    )
}
