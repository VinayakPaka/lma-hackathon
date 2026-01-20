import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/utils'
import {
    LayoutDashboard,
    FileText,
    DollarSign,
    Settings,
    LogOut,
    Leaf,
    Brain,
    Scale,
} from 'lucide-react'

const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/dashboard/upload', icon: Brain, label: 'ESG Analysis', badge: 'AI' },
    { path: '/dashboard/reports', icon: FileText, label: 'ESG Reports' },
    { path: '/dashboard/kpi-benchmarking', icon: Scale, label: 'KPI Assessment', badge: 'NEW' },
    { path: '/dashboard/use-of-proceeds', icon: DollarSign, label: 'Use of Proceeds' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
    const navigate = useNavigate()
    const { logout, user } = useAuthStore()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <aside className="w-64 bg-white border-r border-[#E5E5E5] flex flex-col">
            {/* Logo */}
            <div className="h-20 flex items-center gap-3 px-6">
                <div className="w-10 h-10 rounded-xl bg-kobalt-blue flex items-center justify-center shadow-lg shadow-kobalt-blue/20">
                    <Leaf className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="font-bold text-kobalt-black text-lg">GreenGuard</h1>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 px-4 space-y-1.5">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/dashboard'}
                        className={({ isActive }) =>
                            cn(
                                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                                isActive
                                    ? 'bg-kobalt-blue text-white shadow-md shadow-kobalt-blue/25'
                                    : 'text-kobalt-gray-dark hover:bg-white hover:text-kobalt-black'
                            )
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <item.icon className="w-5 h-5" />
                                <span className="flex-1">{item.label}</span>
                                {'badge' in item && item.badge && (
                                    <span className={cn(
                                        "px-2 py-0.5 text-[10px] font-bold rounded-full",
                                        isActive
                                            ? "bg-white/20 text-white"
                                            : "bg-kobalt-blue/10 text-kobalt-blue"
                                    )}>
                                        {item.badge}
                                    </span>
                                )}
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* User section */}
            <div className="p-4 m-4 bg-white rounded-2xl border border-[#E5E5E5]">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-kobalt-gray flex items-center justify-center text-kobalt-blue font-bold">
                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-kobalt-black truncate">{user?.name || 'User'}</p>
                        <p className="text-xs text-kobalt-gray-dark truncate capitalize">{user?.role || 'Member'}</p>
                    </div>
                </div>
                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center gap-2 w-full px-3 py-2 text-xs font-semibold text-kobalt-gray-dark hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out
                </button>
            </div>
        </aside>
    )
}
