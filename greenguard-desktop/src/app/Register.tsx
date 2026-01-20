import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Leaf } from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltInput } from '@/components/ui/KobaltInput'
import { KobaltButton } from '@/components/ui/KobaltButton'

export default function Register() {
    const navigate = useNavigate()
    const login = useAuthStore((state) => state.login)
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [role, setRole] = useState('borrower')
    const [error, setError] = useState('')

    const registerMutation = useMutation({
        mutationFn: () => authApi.register(name, email, password, role),
        onSuccess: (response) => {
            const { access_token, refresh_token, user } = response.data
            login(user, access_token, refresh_token)
            navigate('/dashboard')
        },
        onError: (err: any) => {
            setError(err.response?.data?.detail || 'Registration failed')
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        registerMutation.mutate()
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#F7F7F5] p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 rounded-2xl bg-kobalt-blue flex items-center justify-center mx-auto mb-4 shadow-lg shadow-kobalt-blue/20">
                        <Leaf className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-kobalt-black">Create Account</h1>
                    <p className="text-kobalt-gray-dark mt-2 font-medium">Join GreenGuard ESG Platform</p>
                </div>

                <KobaltCard padding="lg" className="space-y-6">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {error && (
                            <div className="p-4 bg-red-50 text-red-600 text-sm font-medium rounded-xl border border-red-100 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                {error}
                            </div>
                        )}

                        <KobaltInput
                            label="Full Name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter your name"
                            required
                        />

                        <KobaltInput
                            label="Email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            required
                        />

                        <KobaltInput
                            label="Password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Create a password"
                            required
                            minLength={8}
                        />

                        <div className="space-y-1.5">
                            <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">
                                Role
                            </label>
                            <select
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                className={`
                                    w-full 
                                    bg-kobalt-gray/50 
                                    border border-transparent 
                                    rounded-xl 
                                    px-4 py-3 
                                    text-kobalt-black 
                                    transition-all duration-200
                                    focus:bg-white 
                                    focus:border-kobalt-blue/30 
                                    focus:ring-4 focus:ring-kobalt-blue/10 
                                    focus:outline-none 
                                    appearance-none
                                `}
                            >
                                <option value="borrower">Borrower</option>
                                <option value="bank">Bank</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>

                        <KobaltButton
                            type="submit"
                            disabled={registerMutation.isPending}
                            className="w-full mt-2"
                            isLoading={registerMutation.isPending}
                        >
                            Create Account
                        </KobaltButton>

                        <p className="text-center text-sm text-kobalt-gray-dark font-medium pt-2">
                            Already have an account?{' '}
                            <Link to="/login" className="text-kobalt-blue hover:text-blue-700 transition-colors">
                                Sign In
                            </Link>
                        </p>
                    </form>
                </KobaltCard>
            </div>
        </div>
    )
}
