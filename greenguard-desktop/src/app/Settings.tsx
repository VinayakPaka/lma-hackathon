import { useAuthStore } from '@/store/authStore'
import { User, Shield, Bell, Palette, Info, Lock } from 'lucide-react'
import { KobaltCard } from '@/components/ui/KobaltCard'
import { KobaltButton } from '@/components/ui/KobaltButton'

export default function Settings() {
    const { user } = useAuthStore()

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-12">
            <div>
                <h1 className="text-2xl font-bold text-kobalt-black">Settings</h1>
                <p className="text-kobalt-gray-dark">Manage your account and preferences</p>
            </div>

            {/* Profile Section */}
            <KobaltCard>
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                        <User className="w-5 h-5 text-kobalt-blue" />
                    </div>
                    <h3 className="font-bold text-kobalt-black">Profile</h3>
                </div>
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-kobalt-blue to-blue-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-kobalt-blue/20">
                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div>
                        <p className="font-bold text-kobalt-black text-lg">{user?.name || 'User'}</p>
                        <p className="text-sm text-kobalt-gray-dark">{user?.email || 'user@example.com'}</p>
                        <span className="inline-block mt-2 px-3 py-1 bg-kobalt-blue/10 text-kobalt-blue text-xs font-bold uppercase tracking-wider rounded-lg">
                            {user?.role || 'Member'}
                        </span>
                    </div>
                </div>
            </KobaltCard>

            {/* Security Section */}
            <KobaltCard>
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                        <Shield className="w-5 h-5 text-kobalt-blue" />
                    </div>
                    <h3 className="font-bold text-kobalt-black">Security</h3>
                </div>
                <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 bg-kobalt-gray/30 rounded-xl">
                        <div className="flex items-center gap-3">
                            <Lock className="w-4 h-4 text-kobalt-gray-dark" />
                            <div>
                                <p className="font-bold text-sm text-kobalt-black">Password</p>
                                <p className="text-xs text-kobalt-gray-dark">Last changed: Never</p>
                            </div>
                        </div>
                        <KobaltButton variant="secondary" size="sm">Change</KobaltButton>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-kobalt-gray/30 rounded-xl">
                        <div>
                            <p className="font-bold text-sm text-kobalt-black">Two-Factor Authentication</p>
                            <p className="text-xs text-kobalt-gray-dark">Not enabled</p>
                        </div>
                        <KobaltButton variant="secondary" size="sm">Enable</KobaltButton>
                    </div>
                </div>
            </KobaltCard>

            {/* Notifications Section */}
            <KobaltCard>
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                        <Bell className="w-5 h-5 text-kobalt-blue" />
                    </div>
                    <h3 className="font-bold text-kobalt-black">Notifications</h3>
                </div>
                <div className="space-y-3">
                    {['Email notifications', 'Compliance alerts', 'Report updates'].map((label, i) => (
                        <label key={i} className="flex items-center justify-between p-4 bg-kobalt-gray/30 rounded-xl cursor-pointer hover:bg-kobalt-gray/50 transition-colors">
                            <span className="text-sm font-bold text-kobalt-black">{label}</span>
                            <div className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" defaultChecked className="sr-only peer" />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-kobalt-blue"></div>
                            </div>
                        </label>
                    ))}
                </div>
            </KobaltCard>

            {/* Appearance Section */}
            <KobaltCard>
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                        <Palette className="w-5 h-5 text-kobalt-blue" />
                    </div>
                    <h3 className="font-bold text-kobalt-black">Appearance</h3>
                </div>
                <div className="flex gap-4">
                    <div className="flex-1 p-4 bg-[#F7F7F5] rounded-xl border-2 border-kobalt-blue cursor-pointer relative overflow-hidden group">
                        <div className="absolute top-2 right-2 w-4 h-4 bg-kobalt-blue rounded-full flex items-center justify-center">
                            <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                        </div>
                        <div className="h-20 bg-white rounded-lg border border-gray-200 shadow-sm mb-3"></div>
                        <p className="text-center font-bold text-kobalt-blue text-sm">Light Mode</p>
                    </div>
                    <div className="flex-1 p-4 bg-white rounded-xl border-2 border-transparent hover:border-kobalt-border cursor-not-allowed opacity-50 grayscale">
                        <div className="h-20 bg-gray-900 rounded-lg border border-gray-800 shadow-sm mb-3"></div>
                        <p className="text-center font-medium text-kobalt-gray-dark text-sm">Dark Mode (Coming Soon)</p>
                    </div>
                </div>
            </KobaltCard>

            {/* About Section */}
            <KobaltCard>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-kobalt-blue/10 rounded-lg">
                        <Info className="w-5 h-5 text-kobalt-blue" />
                    </div>
                    <h3 className="font-bold text-kobalt-black">About</h3>
                </div>
                <div className="text-sm text-kobalt-gray-dark space-y-1 pl-1">
                    <p className="font-medium text-kobalt-black">GreenGuard ESG Desktop</p>
                    <p>Version 1.0.0 (Beta)</p>
                    <p>© 2024 GreenGuard. All rights reserved.</p>
                </div>
            </KobaltCard>
        </div>
    )
}
