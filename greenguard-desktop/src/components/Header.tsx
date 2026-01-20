import { Bell, Search } from 'lucide-react'

export default function Header() {
    return (
        <header className="h-20 bg-white border-b border-[#E5E5E5] px-8 flex items-center justify-between">
            {/* Search */}
            <div className="flex-1 max-w-lg">
                <div className="relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-kobalt-gray-dark group-focus-within:text-kobalt-blue transition-colors" />
                    <input
                        type="text"
                        placeholder="Search reports, documents..."
                        className="w-full pl-11 pr-4 py-3 bg-white rounded-xl text-sm text-kobalt-black placeholder:text-gray-400 border border-transparent focus:outline-none focus:ring-4 focus:ring-kobalt-blue/10 focus:border-kobalt-blue/20 transition-all shadow-sm"
                    />
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
                <button className="relative p-2.5 rounded-xl bg-white hover:bg-kobalt-gray border border-transparent hover:border-[#E5E5E5] transition-all group">
                    <Bell className="w-5 h-5 text-kobalt-gray-dark group-hover:text-kobalt-black transition-colors" />
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
                </button>
            </div>
        </header>
    )
}
