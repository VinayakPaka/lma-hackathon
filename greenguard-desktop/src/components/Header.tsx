import { Bell, Search, Moon, Sun } from 'lucide-react'
import { useState } from 'react'

export default function Header() {
    const [isDark, setIsDark] = useState(true)

    const toggleTheme = () => {
        setIsDark(!isDark)
        document.documentElement.classList.toggle('dark')
    }

    return (
        <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between">
            {/* Search */}
            <div className="flex-1 max-w-md">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search reports, documents..."
                        className="w-full pl-10 pr-4 py-2 bg-muted rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
                <button
                    onClick={toggleTheme}
                    className="p-2 rounded-lg hover:bg-muted transition-colors"
                >
                    {isDark ? (
                        <Sun className="w-5 h-5 text-muted-foreground" />
                    ) : (
                        <Moon className="w-5 h-5 text-muted-foreground" />
                    )}
                </button>
                <button className="relative p-2 rounded-lg hover:bg-muted transition-colors">
                    <Bell className="w-5 h-5 text-muted-foreground" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" />
                </button>
            </div>
        </header>
    )
}
