import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { proceedsApi } from '@/lib/api'
import { CheckCircle, XCircle, DollarSign, AlertTriangle } from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltInput } from '@/components/ui/KobaltInput'
import { KobaltButton } from '@/components/ui/KobaltButton'

export default function UseOfProceeds() {
    const [borrowerId, setBorrowerId] = useState('')
    const [vendorName, setVendorName] = useState('')
    const [amount, setAmount] = useState('')
    const [description, setDescription] = useState('')
    const [result, setResult] = useState<any>(null)

    const verifyMutation = useMutation({
        mutationFn: () => proceedsApi.verify(
            Number(borrowerId),
            vendorName,
            Number(amount),
            description
        ),
        onSuccess: (response) => {
            setResult(response.data)
        },
    })

    const handleVerify = (e: React.FormEvent) => {
        e.preventDefault()
        verifyMutation.mutate()
    }

    const handleReset = () => {
        setResult(null)
        setBorrowerId('')
        setVendorName('')
        setAmount('')
        setDescription('')
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
            <div>
                <h1 className="text-2xl font-bold text-kobalt-black">Use-of-Proceeds Verification</h1>
                <p className="text-kobalt-gray-dark">Verify transaction compliance with green loan terms</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Form */}
                <KobaltCard padding="lg">
                    <h3 className="font-bold text-kobalt-black mb-6 flex items-center gap-2">
                        <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                            <DollarSign className="w-5 h-5 text-kobalt-blue" />
                        </div>
                        Transaction Details
                    </h3>

                    <form onSubmit={handleVerify} className="space-y-5">
                        <KobaltInput
                            label="Borrower ID"
                            type="number"
                            value={borrowerId}
                            onChange={(e) => setBorrowerId(e.target.value)}
                            placeholder="Enter borrower ID"
                            required
                        />

                        <KobaltInput
                            label="Vendor Name"
                            type="text"
                            value={vendorName}
                            onChange={(e) => setVendorName(e.target.value)}
                            placeholder="Enter vendor name"
                            required
                        />

                        <KobaltInput
                            label="Transaction Amount ($)"
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            placeholder="Enter amount"
                            required
                            min="0"
                            step="0.01"
                            icon={<DollarSign className="w-4 h-4" />}
                        />

                        <div className="space-y-1.5">
                            <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">
                                Description (Optional)
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the transaction"
                                rows={3}
                                className="w-full bg-kobalt-gray/50 border border-transparent rounded-xl px-4 py-3 text-kobalt-black placeholder:text-gray-400 transition-all duration-200 focus:bg-white focus:border-kobalt-blue/30 focus:ring-4 focus:ring-kobalt-blue/10 focus:outline-none resize-none"
                            />
                        </div>

                        <KobaltButton
                            type="submit"
                            isLoading={verifyMutation.isPending}
                            className="w-full h-12 text-lg"
                        >
                            Verify Transaction
                        </KobaltButton>
                    </form>
                </KobaltCard>

                {/* Results */}
                <div className="space-y-4">
                    {result ? (
                        <>
                            {/* Compliance Status */}
                            <KobaltCard className={`border-2 ${result.is_green_compliant ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                                <div className="flex items-center gap-4">
                                    {result.is_green_compliant ? (
                                        <CheckCircle className="w-12 h-12 text-green-600" />
                                    ) : (
                                        <XCircle className="w-12 h-12 text-red-600" />
                                    )}
                                    <div>
                                        <p className={`text-lg font-bold ${result.is_green_compliant ? 'text-green-700' : 'text-red-700'}`}>
                                            {result.is_green_compliant ? 'GREEN COMPLIANT' : 'NON-COMPLIANT'}
                                        </p>
                                        <p className={`text-sm ${result.is_green_compliant ? 'text-green-600/80' : 'text-red-600/80'}`}>
                                            Transaction #{result.transaction_id}
                                        </p>
                                    </div>
                                </div>
                            </KobaltCard>

                            {/* Scores */}
                            <div className="grid grid-cols-2 gap-4">
                                <KobaltCard className="text-center">
                                    <p className="text-xs font-bold text-kobalt-gray-dark uppercase">Misuse Risk Score</p>
                                    <p className={`text-3xl font-bold mt-2 ${result.misuse_risk_score < 30 ? 'text-green-600' :
                                        result.misuse_risk_score < 60 ? 'text-yellow-600' : 'text-red-600'
                                        }`}>
                                        {result.misuse_risk_score?.toFixed(1)}
                                    </p>
                                </KobaltCard>
                                <KobaltCard className="text-center">
                                    <p className="text-xs font-bold text-kobalt-gray-dark uppercase">Vendor Status</p>
                                    <p className={`text-xl font-bold mt-2 ${result.vendor_status === 'approved' ? 'text-green-600' :
                                        result.vendor_status === 'unknown' ? 'text-yellow-600' : 'text-red-600'
                                        }`}>
                                        {result.vendor_status?.toUpperCase()}
                                    </p>
                                </KobaltCard>
                            </div>

                            {/* Notes */}
                            <KobaltCard>
                                <p className="text-xs font-bold text-kobalt-gray-dark uppercase mb-2">Compliance Notes</p>
                                <p className="text-sm text-kobalt-black leading-relaxed">{result.compliance_notes}</p>
                            </KobaltCard>

                            {/* Recommendations */}
                            {result.recommendations?.length > 0 && (
                                <KobaltCard className="border-l-4 border-l-yellow-400">
                                    <p className="text-sm font-bold text-kobalt-black mb-3 flex items-center gap-2">
                                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                                        Recommendations
                                    </p>
                                    <ul className="space-y-2">
                                        {result.recommendations.map((rec: string, i: number) => (
                                            <li key={i} className="text-sm text-kobalt-gray-dark flex items-start gap-2">
                                                <span className="text-kobalt-blue font-bold">•</span>
                                                {rec}
                                            </li>
                                        ))}
                                    </ul>
                                </KobaltCard>
                            )}

                            <KobaltButton
                                variant="secondary"
                                onClick={handleReset}
                                className="w-full"
                            >
                                Verify Another Transaction
                            </KobaltButton>
                        </>
                    ) : (
                        <KobaltCard className="h-full flex flex-col items-center justify-center text-center p-12 border-dashed">
                            <div className="w-16 h-16 bg-kobalt-gray/50 rounded-full flex items-center justify-center mb-4">
                                <DollarSign className="w-8 h-8 text-kobalt-gray-dark" />
                            </div>
                            <p className="text-lg font-bold text-kobalt-black">Enter Transaction Details</p>
                            <p className="text-sm text-kobalt-gray-dark mt-1">
                                Fill in the form to verify green compliance
                            </p>
                        </KobaltCard>
                    )}
                </div>
            </div>
        </div>
    )
}
