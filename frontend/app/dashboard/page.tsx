'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { AnalyticsOverview } from '@/lib/types'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']

export default function DashboardPage() {
    const router = useRouter()
    const [stats, setStats] = useState<AnalyticsOverview | null>(null)
    const [deptData, setDeptData] = useState<any[]>([])
    const [enrollmentData, setEnrollmentData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Check authentication
        const token = localStorage.getItem('access_token')
        if (!token) {
            router.push('/login')
            return
        }

        loadData()
    }, [router])

    const loadData = async () => {
        try {
            const [overviewRes, deptRes, enrollRes] = await Promise.all([
                api.get('/api/analytics/overview'),
                api.get('/api/analytics/department-distribution'),
                api.get('/api/analytics/enrollment-trends?months=6'),
            ])

            setStats(overviewRes.data)
            setDeptData(deptRes.data)
            setEnrollmentData(enrollRes.data)
        } catch (error) {
            console.error('Error loading data:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/login')
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-white"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen p-6">
            {/* Header */}
            <div className="glass-card-white mb-6 p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gradient">CS Department Dashboard</h1>
                        <p className="text-gray-600 mt-1">Computer Science Department — Overview & Analytics</p>
                    </div>
                    <div className="flex flex-wrap gap-2 md:gap-3">
                        <button
                            onClick={() => router.push('/dashboard/students')}
                            className="px-6 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition"
                        >
                            Students
                        </button>
                        <button
                            onClick={() => router.push('/dashboard/calendar')}
                            className="px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition"
                        >
                            Calendar
                        </button>
                        <button
                            onClick={() => router.push('/dashboard/vouchers')}
                            className="px-6 py-3 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 transition"
                        >
                            Vouchers
                        </button>
                        <button
                            onClick={() => router.push('/chat')}
                            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition"
                        >
                            AI Chat
                        </button>
                        <button
                            onClick={handleLogout}
                            className="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div className="stat-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Total Students</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total_students || 0}</p>
                        </div>
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">👥</span>
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Active Students</p>
                            <p className="text-3xl font-bold text-green-600 mt-2">{stats?.active_students || 0}</p>
                        </div>
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">✓</span>
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Average GPA</p>
                            <p className="text-3xl font-bold text-purple-600 mt-2">{stats?.average_gpa.toFixed(2) || '0.00'}</p>
                        </div>
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">📊</span>
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Recent Enrollments</p>
                            <p className="text-3xl font-bold text-orange-600 mt-2">{stats?.recent_enrollments || 0}</p>
                        </div>
                        <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">📈</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="grid lg:grid-cols-2 gap-6 mb-6">
                {/* Department Distribution */}
                <div className="glass-card-white p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Students by Degree Program</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={deptData}
                                dataKey="count"
                                nameKey="department"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label
                            >
                                {deptData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Enrollment Trends */}
                <div className="glass-card-white p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Enrollment Trends</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={enrollmentData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="enrollments" stroke="#0ea5e9" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="glass-card-white p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid md:grid-cols-3 gap-4">
                    <button
                        onClick={() => router.push('/dashboard/students')}
                        className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl hover:shadow-lg transition text-left"
                    >
                        <span className="text-2xl mb-2 block">📝</span>
                        <p className="font-semibold text-gray-900">Manage Students</p>
                        <p className="text-sm text-gray-600 mt-1">Add, edit, or remove student records</p>
                    </button>

                    <button
                        onClick={() => router.push('/dashboard/reports')}
                        className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl hover:shadow-lg transition text-left"
                    >
                        <span className="text-2xl mb-2 block">📄</span>
                        <p className="font-semibold text-gray-900">Generate Reports</p>
                        <p className="text-sm text-gray-600 mt-1">Create PDF reports for analysis</p>
                    </button>

                    <button
                        onClick={() => router.push('/chat')}
                        className="p-4 bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl hover:shadow-lg transition text-left"
                    >
                        <span className="text-2xl mb-2 block">🤖</span>
                        <p className="font-semibold text-gray-900">AI Assistant</p>
                        <p className="text-sm text-gray-600 mt-1">Use natural language commands</p>
                    </button>

                    <button
                        onClick={() => router.push('/dashboard/vouchers')}
                        className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl hover:shadow-lg transition text-left"
                    >
                        <span className="text-2xl mb-2 block">💰</span>
                        <p className="font-semibold text-gray-900">Fee Vouchers</p>
                        <p className="text-sm text-gray-600 mt-1">Review student fee submissions</p>
                    </button>
                </div>
            </div>
        </div>
    )
}
