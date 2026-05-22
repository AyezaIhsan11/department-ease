'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

export default function ReportsPage() {
    const router = useRouter()
    const [loading, setLoading] = useState<string | null>(null)
    const [year, setYear] = useState(new Date().getFullYear())
    const [month, setMonth] = useState(new Date().getMonth() + 1)

    const downloadReport = async (type: 'monthly' | 'yearly' | 'student-list') => {
        setLoading(type)

        try {
            let url = ''
            let filename = ''

            if (type === 'monthly') {
                url = `/api/reports/monthly?year=${year}&month=${month}`
                filename = `monthly_report_${year}_${month}.pdf`
            } else if (type === 'yearly') {
                url = `/api/reports/yearly?year=${year}`
                filename = `yearly_report_${year}.pdf`
            } else {
                url = '/api/reports/student-list'
                filename = 'student_list.pdf'
            }

            const response = await api.get(url, {
                responseType: 'blob'
            })

            const blob = new Blob([response.data], { type: 'application/pdf' })
            const downloadUrl = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = downloadUrl
            link.setAttribute('download', filename)
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (error) {
            alert('Error generating report')
        } finally {
            setLoading(null)
        }
    }

    return (
        <div className="min-h-screen p-6">
            {/* Header */}
            <div className="glass-card-white mb-6 p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gradient">PDF Reports</h1>
                        <p className="text-gray-600 mt-1">Generate and download reports</p>
                    </div>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition w-full sm:w-auto text-center"
                    >
                        ← Back to Dashboard
                    </button>
                </div>
            </div>

            {/* Report Options */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Monthly Report */}
                <div className="glass-card-white p-6">
                    <div className="text-4xl mb-4">📅</div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Monthly Report</h3>
                    <p className="text-gray-600 mb-4">Generate report for a specific month</p>

                    <div className="space-y-3 mb-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                            <input
                                type="number"
                                value={year}
                                onChange={(e) => setYear(parseInt(e.target.value))}
                                className="input-field-white"
                                min="2000"
                                max="2100"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Month</label>
                            <select
                                value={month}
                                onChange={(e) => setMonth(parseInt(e.target.value))}
                                className="input-field-white"
                            >
                                {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                                    <option key={m} value={m}>
                                        {new Date(2024, m - 1).toLocaleString('default', { month: 'long' })}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <button
                        onClick={() => downloadReport('monthly')}
                        disabled={loading === 'monthly'}
                        className="w-full px-6 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition disabled:opacity-50"
                    >
                        {loading === 'monthly' ? 'Generating...' : 'Download PDF'}
                    </button>
                </div>

                {/* Yearly Report */}
                <div className="glass-card-white p-6">
                    <div className="text-4xl mb-4">📊</div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Yearly Report</h3>
                    <p className="text-gray-600 mb-4">Generate annual summary report</p>

                    <div className="space-y-3 mb-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                            <input
                                type="number"
                                value={year}
                                onChange={(e) => setYear(parseInt(e.target.value))}
                                className="input-field-white"
                                min="2000"
                                max="2100"
                            />
                        </div>
                    </div>

                    <button
                        onClick={() => downloadReport('yearly')}
                        disabled={loading === 'yearly'}
                        className="w-full px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition disabled:opacity-50 mt-12"
                    >
                        {loading === 'yearly' ? 'Generating...' : 'Download PDF'}
                    </button>
                </div>

                {/* Student List */}
                <div className="glass-card-white p-6">
                    <div className="text-4xl mb-4">📋</div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Student Directory</h3>
                    <p className="text-gray-600 mb-4">Complete list of all students</p>

                    <div className="mb-4 pt-24">
                        <p className="text-sm text-gray-500">
                            This report includes all current student records with their details.
                        </p>
                    </div>

                    <button
                        onClick={() => downloadReport('student-list')}
                        disabled={loading === 'student-list'}
                        className="w-full px-6 py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition disabled:opacity-50"
                    >
                        {loading === 'student-list' ? 'Generating...' : 'Download PDF'}
                    </button>
                </div>
            </div>
        </div>
    )
}
