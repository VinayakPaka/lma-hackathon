import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './app/Dashboard'
import Upload from './app/Upload'
import Reports from './app/Reports'
import ReportDetail from './app/ReportDetail'
import KPITool from './app/KPITool'
import UseOfProceeds from './app/UseOfProceeds'
import Settings from './app/Settings'

// Auth is bypassed for testing - no login/register screens
function App() {
    return (
        <div className="min-h-screen bg-background dark">
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="upload" element={<Upload />} />
                    <Route path="reports" element={<Reports />} />
                    <Route path="reports/:id" element={<ReportDetail />} />
                    <Route path="kpi" element={<KPITool />} />
                    <Route path="use-of-proceeds" element={<UseOfProceeds />} />
                    <Route path="settings" element={<Settings />} />
                </Route>
                {/* Catch all - redirect to dashboard */}
                <Route path="*" element={<Dashboard />} />
            </Routes>
        </div>
    )
}

export default App
