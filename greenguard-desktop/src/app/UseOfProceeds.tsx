import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { proceedsApi } from '@/lib/api'
import { CheckCircle, XCircle, Loader2, DollarSign, AlertTriangle } from 'lucide-react'

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
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold">Use-of-Proceeds Verification</h1>
                <p className="text-muted-foreground">Verify transaction compliance with green loan terms</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Form */}
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-primary" />
                        Transaction Details
                    </h3>

                    <form onSubmit={handleVerify} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Borrower ID</label>
                            <input
                                type="number"
                                value={borrowerId}
                                onChange={(e) => setBorrowerId(e.target.value)}
                                placeholder="Enter borrower ID"
                                required
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Vendor Name</label>
                            <input
                                type="text"
                                value={vendorName}
                                onChange={(e) => setVendorName(e.target.value)}
                                placeholder="Enter vendor name"
                                required
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Transaction Amount ($)</label>
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder="Enter amount"
                                required
                                min="0"
                                step="0.01"
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Description (Optional)</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the transaction"
                                rows={3}
                                className="w-full px-4 py-2.5 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={verifyMutation.isPending}
                            className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {verifyMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                            Verify Transaction
                        </button>
                    </form>
                </div>

                {/* Results */}
                <div className="space-y-4">
                    {result ? (
                        <>
                            {/* Compliance Status */}
                            <div className={`rounded-xl p-6 border ${result.is_green_compliant
                                    ? 'bg-green-500/5 border-green-500/20'
                                    : 'bg-red-500/5 border-red-500/20'
                                }`}>
                                <div className="flex items-center gap-4">
                                    {result.is_green_compliant ? (
                                        <CheckCircle className="w-12 h-12 text-green-500" />
                                    ) : (
                                        <XCircle className="w-12 h-12 text-red-500" />
                                    )}
                                    <div>
                                        <p className="text-lg font-bold">
                                            {result.is_green_compliant ? 'GREEN COMPLIANT' : 'NON-COMPLIANT'}
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            Transaction #{result.transaction_id}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Scores */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-card rounded-xl p-4 border border-border text-center">
                                    <p className="text-sm text-muted-foreground">Misuse Risk Score</p>
                                    <p className={`text-2xl font-bold mt-1 ${result.misuse_risk_score < 30 ? 'text-green-500' :
                                            result.misuse_risk_score < 60 ? 'text-yellow-500' : 'text-red-500'
                                        }`}>
                                        {result.misuse_risk_score?.toFixed(1)}
                                    </p>
                                </div>
                                <div className="bg-card rounded-xl p-4 border border-border text-center">
                                    <p className="text-sm text-muted-foreground">Vendor Status</p>
                                    <p className={`text-lg font-bold mt-1 ${result.vendor_status === 'approved' ? 'text-green-500' :
                                            result.vendor_status === 'unknown' ? 'text-yellow-500' : 'text-red-500'
                                        }`}>
                                        {result.vendor_status?.toUpperCase()}
                                    </p>
                                </div>
                            </div>

                            {/* Notes */}
                            <div className="bg-card rounded-xl p-4 border border-border">
                                <p className="text-sm font-medium mb-2">Compliance Notes</p>
                                <p className="text-sm text-muted-foreground">{result.compliance_notes}</p>
                            </div>

                            {/* Recommendations */}
                            {result.recommendations?.length > 0 && (
                                <div className="bg-card rounded-xl p-4 border border-border">
                                    <p className="text-sm font-medium mb-2 flex items-center gap-2">
                                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                                        Recommendations
                                    </p>
                                    <ul className="space-y-2">
                                        {result.recommendations.map((rec: string, i: number) => (
                                            <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                                <span className="text-primary">•</span>
                                                {rec}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            <button
                                onClick={handleReset}
                                className="w-full py-2 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
                            >
                                Verify Another Transaction
                            </button>
                        </>
                    ) : (
                        <div className="bg-card rounded-xl p-12 border border-border text-center">
                            <DollarSign className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-lg font-medium">Enter Transaction Details</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Fill in the form to verify green compliance
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
