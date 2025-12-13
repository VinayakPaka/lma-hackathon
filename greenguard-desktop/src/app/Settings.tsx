import { useAuthStore } from '@/store/authStore'
import { User, Shield, Bell, Palette, Info } from 'lucide-react'

export default function Settings() {
    const { user } = useAuthStore()

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold">Settings</h1>
                <p className="text-muted-foreground">Manage your account and preferences</p>
            </div>

            {/* Profile Section */}
            <div className="bg-card rounded-xl p-6 border border-border">
                <div className="flex items-center gap-3 mb-4">
                    <User className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Profile</h3>
                </div>
                <div className="space-y-4">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                            <span className="text-2xl font-bold text-primary">
                                {user?.name?.charAt(0).toUpperCase() || 'U'}
                            </span>
                        </div>
                        <div>
                            <p className="font-medium">{user?.name || 'User'}</p>
                            <p className="text-sm text-muted-foreground">{user?.email || 'user@example.com'}</p>
                            <span className="inline-block mt-1 px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                                {user?.role || 'Member'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Security Section */}
            <div className="bg-card rounded-xl p-6 border border-border">
                <div className="flex items-center gap-3 mb-4">
                    <Shield className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Security</h3>
                </div>
                <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div>
                            <p className="font-medium text-sm">Password</p>
                            <p className="text-xs text-muted-foreground">Last changed: Never</p>
                        </div>
                        <button className="text-sm text-primary hover:underline">Change</button>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div>
                            <p className="font-medium text-sm">Two-Factor Authentication</p>
                            <p className="text-xs text-muted-foreground">Not enabled</p>
                        </div>
                        <button className="text-sm text-primary hover:underline">Enable</button>
                    </div>
                </div>
            </div>

            {/* Notifications Section */}
            <div className="bg-card rounded-xl p-6 border border-border">
                <div className="flex items-center gap-3 mb-4">
                    <Bell className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Notifications</h3>
                </div>
                <div className="space-y-3">
                    <label className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer">
                        <span className="text-sm font-medium">Email notifications</span>
                        <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
                    </label>
                    <label className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer">
                        <span className="text-sm font-medium">Compliance alerts</span>
                        <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
                    </label>
                    <label className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer">
                        <span className="text-sm font-medium">Report updates</span>
                        <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
                    </label>
                </div>
            </div>

            {/* Appearance Section */}
            <div className="bg-card rounded-xl p-6 border border-border">
                <div className="flex items-center gap-3 mb-4">
                    <Palette className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Appearance</h3>
                </div>
                <div className="flex gap-3">
                    <button className="flex-1 p-3 bg-muted rounded-lg text-sm font-medium border-2 border-primary">
                        Dark Mode
                    </button>
                    <button className="flex-1 p-3 bg-muted rounded-lg text-sm font-medium border-2 border-transparent hover:border-border">
                        Light Mode
                    </button>
                </div>
            </div>

            {/* About Section */}
            <div className="bg-card rounded-xl p-6 border border-border">
                <div className="flex items-center gap-3 mb-4">
                    <Info className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">About</h3>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                    <p><strong>GreenGuard ESG Desktop</strong></p>
                    <p>Version 1.0.0</p>
                    <p>© 2024 GreenGuard. All rights reserved.</p>
                </div>
            </div>
        </div>
    )
}
