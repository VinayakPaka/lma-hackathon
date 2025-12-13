import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { kpiApi } from '@/lib/api'
import { ESGBarChart } from '@/components/ESGMetricChart'
import { BarChart3, Loader2, Target, TrendingUp } from 'lucide-react'

export default function KPITool() {
    const [sector, setSector] = useState('')
    const [metric, setMetric] = useState('')
    const [benchmarkResult, setBenchmarkResult] = useState<any>(null)

    const { data: sectorsData } = useQuery({
        queryKey: ['kpi-sectors'],
        queryFn: () => kpiApi.getSectors(),
    })

    const { data: metricsData } = useQuery({
        queryKey: ['kpi-metrics', sector],
        queryFn: () => kpiApi.getMetrics(sector),
        enabled: !!sector,
    })

    const benchmarkMutation = useMutation({
        mutationFn: () => kpiApi.benchmark(sector, metric),
        onSuccess: (response) => {
            setBenchmarkResult(response.data)
        },
    })

    const sectors = sectorsData?.data || ['manufacturing', 'financial_services', 'real_estate', 'transportation', 'technology']
    const metrics = metricsData?.data || ['co2_reduction', 'energy_efficiency', 'renewable_energy', 'waste_recycling']

    const handleGetBenchmark = () => {
        if (sector && metric) {
            benchmarkMutation.mutate()
        }
    }

    const chartData = benchmarkResult ? [
        { name: 'Baseline Low', value: benchmarkResult.baseline_range?.min || 0 },
        { name: 'Baseline High', value: benchmarkResult.baseline_range?.max || 0 },
        { name: 'Market Avg', value: benchmarkResult.market_average || 0 },
        { name: 'Ambitious', value: benchmarkResult.ambitious_target || 0 },
    ] : []

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold">KPI Benchmarking Tool</h1>
                <p className="text-muted-foreground">Compare your ESG metrics against industry standards</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Input Form */}
                <div className="bg-card rounded-xl p-6 border border-border space-y-4">
                    <h3 className="font-semibold flex items-center gap-2">
                        <Target className="w-5 h-5 text-primary" />
                        Select Parameters
                    </h3>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Industry Sector</label>
                        <select
                            value={sector}
                            onChange={(e) => { setSector(e.target.value); setMetric('') }}
                            className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                        >
                            <option value="">Select sector...</option>
                            {sectors.map((s: string) => (
                                <option key={s} value={s}>
                                    {s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">KPI Metric</label>
                        <select
                            value={metric}
                            onChange={(e) => setMetric(e.target.value)}
                            disabled={!sector}
                            className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
                        >
                            <option value="">Select metric...</option>
                            {metrics.map((m: string) => (
                                <option key={m} value={m}>
                                    {m.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleGetBenchmark}
                        disabled={!sector || !metric || benchmarkMutation.isPending}
                        className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {benchmarkMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                        Get Benchmark
                    </button>
                </div>

                {/* Results */}
                <div className="lg:col-span-2 space-y-4">
                    {benchmarkResult ? (
                        <>
                            <div className="bg-card rounded-xl p-6 border border-border">
                                <h3 className="font-semibold mb-4 flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-primary" />
                                    Benchmark Results: {metric.replace(/_/g, ' ')}
                                </h3>
                                <ESGBarChart data={chartData} />
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-card rounded-xl p-4 border border-border text-center">
                                    <p className="text-sm text-muted-foreground">Baseline Range</p>
                                    <p className="text-xl font-bold text-primary mt-1">
                                        {benchmarkResult.baseline_range?.min} - {benchmarkResult.baseline_range?.max}%
                                    </p>
                                </div>
                                <div className="bg-card rounded-xl p-4 border border-border text-center">
                                    <p className="text-sm text-muted-foreground">Market Average</p>
                                    <p className="text-xl font-bold text-yellow-500 mt-1">
                                        {benchmarkResult.market_average}%
                                    </p>
                                </div>
                                <div className="bg-card rounded-xl p-4 border border-border text-center">
                                    <p className="text-sm text-muted-foreground">Ambitious Target</p>
                                    <p className="text-xl font-bold text-green-500 mt-1">
                                        {benchmarkResult.ambitious_target}%
                                    </p>
                                </div>
                            </div>

                            <div className="bg-card rounded-xl p-4 border border-border">
                                <div className="flex items-start gap-3">
                                    <TrendingUp className="w-5 h-5 text-primary mt-0.5" />
                                    <div>
                                        <p className="font-medium">Recommendation</p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {benchmarkResult.recommendation}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="bg-card rounded-xl p-12 border border-border text-center">
                            <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-lg font-medium">Select Parameters</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Choose a sector and metric to view benchmarks
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
