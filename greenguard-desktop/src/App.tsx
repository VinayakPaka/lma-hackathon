import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './app/Dashboard'
import Upload from './app/Upload'
import Reports from './app/Reports'
import ReportDetail from './app/ReportDetail'
import KPITool from './app/KPITool'
import KPIBenchmarking from './app/KPIBenchmarking'
import UseOfProceeds from './app/UseOfProceeds'
import Settings from './app/Settings'
import Login from './app/Login'
import Register from './app/Register'
import LandingPage from './app/LandingPage'

function App() {
    return (
        <div className="min-h-screen bg-background dark">
            <Routes>
                {/* Landing page as the default public route */}
                <Route path="/" element={<LandingPage />} />

                {/* Public routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected routes */}
                <Route element={<ProtectedRoute />}>
                    <Route path="/dashboard" element={<Layout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="upload" element={<Upload />} />
                        <Route path="reports" element={<Reports />} />
                        <Route path="reports/:id" element={<ReportDetail />} />
                        <Route path="kpi" element={<KPITool />} />
                        <Route path="kpi-benchmarking" element={<KPIBenchmarking />} />
                        <Route path="use-of-proceeds" element={<UseOfProceeds />} />
                        <Route path="settings" element={<Settings />} />
                    </Route>
                </Route>

                {/* Redirect unknown routes to landing */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </div>
    )
}

export default App
