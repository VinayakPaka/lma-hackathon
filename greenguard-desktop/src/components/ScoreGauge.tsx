import { cn } from '@/lib/utils'

interface ScoreGaugeProps {
    score: number
    size?: 'sm' | 'md' | 'lg'
    label?: string
    showGrade?: boolean
}

export default function ScoreGauge({ score, size = 'md', label, showGrade = true }: ScoreGaugeProps) {
    const normalizedScore = Math.min(100, Math.max(0, score))
    const circumference = 2 * Math.PI * 45
    const offset = circumference - (normalizedScore / 100) * circumference

    const getColor = (s: number) => {
        if (s >= 80) return 'text-green-500'
        if (s >= 60) return 'text-yellow-500'
        if (s >= 40) return 'text-orange-500'
        return 'text-red-500'
    }

    const getStrokeColor = (s: number) => {
        if (s >= 80) return 'stroke-green-500'
        if (s >= 60) return 'stroke-yellow-500'
        if (s >= 40) return 'stroke-orange-500'
        return 'stroke-red-500'
    }

    const getGrade = (s: number) => {
        if (s >= 90) return 'A'
        if (s >= 80) return 'B'
        if (s >= 70) return 'C'
        if (s >= 60) return 'D'
        return 'F'
    }

    const sizeClasses = {
        sm: 'w-20 h-20',
        md: 'w-32 h-32',
        lg: 'w-44 h-44',
    }

    const textSizes = {
        sm: 'text-lg',
        md: 'text-2xl',
        lg: 'text-4xl',
    }

    return (
        <div className="flex flex-col items-center gap-2">
            <div className={cn('relative', sizeClasses[size])}>
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    {/* Background circle */}
                    <circle
                        cx="50"
                        cy="50"
                        r="45"
                        fill="none"
                        strokeWidth="8"
                        className="stroke-muted"
                    />
                    {/* Progress circle */}
                    <circle
                        cx="50"
                        cy="50"
                        r="45"
                        fill="none"
                        strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        className={cn('transition-all duration-700 ease-out', getStrokeColor(normalizedScore))}
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={cn('font-bold', textSizes[size], getColor(normalizedScore))}>
                        {normalizedScore.toFixed(0)}
                    </span>
                    {showGrade && (
                        <span className="text-xs text-muted-foreground">
                            Grade: {getGrade(normalizedScore)}
                        </span>
                    )}
                </div>
            </div>
            {label && <span className="text-sm font-medium text-muted-foreground">{label}</span>}
        </div>
    )
}
