import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
} from 'recharts'

interface ESGData {
    subject: string
    score: number
    fullMark: number
}

interface ESGMetricChartProps {
    data: ESGData[]
    type?: 'radar' | 'bar'
}

export function ESGRadarChart({ data }: { data: ESGData[] }) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                    dataKey="subject"
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                />
                <PolarRadiusAxis
                    angle={30}
                    domain={[0, 100]}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                />
                <Radar
                    name="ESG Score"
                    dataKey="score"
                    stroke="hsl(142 76% 36%)"
                    fill="hsl(142 76% 36%)"
                    fillOpacity={0.3}
                    strokeWidth={2}
                />
            </RadarChart>
        </ResponsiveContainer>
    )
}

export function ESGBarChart({ data }: { data: { name: string; value: number; benchmark?: number }[] }) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                    dataKey="name"
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                    }}
                />
                <Legend />
                <Bar dataKey="value" fill="hsl(142 76% 36%)" radius={[4, 4, 0, 0]} name="Actual" />
                {data[0]?.benchmark !== undefined && (
                    <Bar dataKey="benchmark" fill="hsl(var(--muted-foreground))" radius={[4, 4, 0, 0]} name="Benchmark" />
                )}
            </BarChart>
        </ResponsiveContainer>
    )
}

export default function ESGMetricChart({ data, type = 'radar' }: ESGMetricChartProps) {
    if (type === 'bar') {
        return <ESGBarChart data={data.map(d => ({ name: d.subject, value: d.score }))} />
    }
    return <ESGRadarChart data={data} />
}
