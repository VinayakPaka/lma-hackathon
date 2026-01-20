import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Leaf } from 'lucide-react'
import { motion } from 'framer-motion'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'
import { KobaltInput } from '@/components/ui/KobaltInput'

export default function Login() {
    const navigate = useNavigate()
    const login = useAuthStore((state) => state.login)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    const loginMutation = useMutation({
        mutationFn: () => authApi.login(email, password),
        onSuccess: (response) => {
            const { access_token, refresh_token, user } = response.data
            login(user, access_token, refresh_token)
            navigate('/dashboard')
        },
        onError: (err: any) => {
            setError(err.response?.data?.detail || 'Login failed')
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        loginMutation.mutate()
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-kobalt-gray p-4 relative overflow-hidden">
            {/* Background Gradient Blob */}
            <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-kobalt-blue/10 to-transparent pointer-events-none" />

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white shadow-sm mb-6">
                        <Leaf className="w-8 h-8 text-kobalt-blue" />
                    </div>
                    <h1 className="text-3xl font-medium tracking-tight text-kobalt-black">GreenGuard</h1>
                    <p className="text-kobalt-black/60 mt-2 text-lg">Sign in to your dashboard</p>
                </div>

                <KobaltCard padding="lg" className="shadow-lg border-opacity-60">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="p-4 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100 flex items-center gap-2"
                            >
                                <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                {error}
                            </motion.div>
                        )}

                        <div className="space-y-4">
                            <KobaltInput
                                label="Work Email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                required
                                autoFocus
                            />

                            <div className="space-y-1">
                                <KobaltInput
                                    label="Password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter your password"
                                    required
                                />
                                <div className="flex justify-end">
                                    <Link to="/forgot-password" className="text-xs text-kobalt-blue hover:text-blue-700 font-medium transition-colors">
                                        Forgot password?
                                    </Link>
                                </div>
                            </div>
                        </div>

                        <div className="pt-2">
                            <KobaltButton
                                type="submit"
                                className="w-full py-3 text-base"
                                isLoading={loginMutation.isPending}
                            >
                                Sign In
                            </KobaltButton>
                        </div>
                    </form>
                </KobaltCard>

                <p className="text-center mt-8 text-sm text-kobalt-black/50">
                    Don't have an account?{' '}
                    <Link to="/register" className="text-kobalt-blue font-semibold hover:underline">
                        Contact Sales
                    </Link>
                </p>
            </motion.div>

            <div className="absolute bottom-8 text-xs text-kobalt-black/30 font-medium">
                © 2026 GreenGuard ESG Platform
            </div>
        </div>
    )
}
