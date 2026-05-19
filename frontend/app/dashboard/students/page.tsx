'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Student } from '@/lib/types'

export default function StudentsPage() {
    const router = useRouter()
    const [students, setStudents] = useState<Student[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [department, setDepartment] = useState('')
    const [page, setPage] = useState(1)
    const [total, setTotal] = useState(0)
    const [totalPages, setTotalPages] = useState(0)
    const [importing, setImporting] = useState(false)
    const [importResult, setImportResult] = useState<{ created_count: number; total_rows: number; errors: string[] } | null>(null)
    const csvInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        loadStudents()
    }, [page, search, department])

    const loadStudents = async () => {
        try {
            const params: any = { page, page_size: 10 }
            if (search) params.search = search
            if (department) params.department = department

            const response = await api.get('/api/students', { params })
            setStudents(response.data.students)
            setTotal(response.data.total)
            setTotalPages(response.data.total_pages)
        } catch (error) {
            console.error('Error loading students:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (studentId: string) => {
        if (!confirm('Are you sure you want to delete this student?')) return

        try {
            await api.delete(`/api/students/${studentId}`)
            loadStudents()
        } catch (error) {
            alert('Error deleting student')
        }
    }

    const handleExport = async () => {
        try {
            const response = await api.get('/api/students/export/csv', {
                responseType: 'blob'
            })

            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', 'students.csv')
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (error) {
            alert('Error exporting students')
        }
    }

    const handleDownloadTemplate = () => {
        const headers = 'student_id,first_name,last_name,email,department,year,gpa,contact_number,address'
        const example = 'CS001,John,Doe,john.doe@example.com,Computer Science,1,3.5,+92-300-1234567,123 Main St'
        const csvContent = `${headers}\n${example}`
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'students_template.csv')
        document.body.appendChild(link)
        link.click()
        link.remove()
    }

    const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setImporting(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await api.post('/api/students/upload/csv', formData)
            setImportResult(response.data)
            loadStudents()
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error importing CSV')
        } finally {
            setImporting(false)
            // reset input so same file can be re-selected
            if (csvInputRef.current) csvInputRef.current.value = ''
        }
    }

    return (
        <>
            <div className="min-h-screen p-6">
                {/* Header */}
            <div className="glass-card-white mb-6 p-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gradient">Student Management</h1>
                        <p className="text-gray-600 mt-1">Manage all student records</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                        >
                            ← Back
                        </button>
                        <button
                            onClick={handleDownloadTemplate}
                            className="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 transition text-sm"
                        >
                            📄 CSV Template
                        </button>
                        <button
                            onClick={() => csvInputRef.current?.click()}
                            disabled={importing}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50"
                        >
                            {importing ? '⏳ Importing...' : '📥 Import CSV'}
                        </button>
                        <input
                            type="file"
                            accept=".csv"
                            ref={csvInputRef}
                            onChange={handleImportCSV}
                            className="hidden"
                        />
                        <button
                            onClick={handleExport}
                            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                        >
                            📤 Export CSV
                        </button>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex gap-4">
                    <input
                        type="text"
                        placeholder="Search by name, ID, or email..."
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value)
                            setPage(1)
                        }}
                        className="flex-1 input-field-white"
                    />
                    <select
                        value={department}
                        onChange={(e) => {
                            setDepartment(e.target.value)
                            setPage(1)
                        }}
                        className="input-field-white"
                    >
                        <option value="">All Departments</option>
                        <option value="Computer Science">Computer Science</option>
                        <option value="Engineering">Engineering</option>
                        <option value="Mathematics">Mathematics</option>
                        <option value="Physics">Physics</option>
                    </select>
                </div>
            </div>

            {/* Student Table */}
            <div className="glass-card-white p-6">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b-2 border-gray-200">
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Student ID</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Name</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Mobile Number</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Department</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Year</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">GPA</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={9} className="text-center py-8">
                                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                                    </td>
                                </tr>
                            ) : students.length === 0 ? (
                                <tr>
                                    <td colSpan={9} className="text-center py-8 text-gray-500">
                                        No students found
                                    </td>
                                </tr>
                            ) : (
                                students.map((student) => (
                                    <tr key={student.id} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-3 px-4 font-medium">{student.student_id}</td>
                                        <td className="py-3 px-4">{student.first_name} {student.last_name}</td>
                                        <td className="py-3 px-4 text-sm text-gray-600">{student.email}</td>
                                        <td className="py-3 px-4 text-sm text-gray-600">{student.contact_number || 'N/A'}</td>
                                        <td className="py-3 px-4">{student.department}</td>
                                        <td className="py-3 px-4">{student.year}</td>
                                        <td className="py-3 px-4">{student.gpa?.toFixed(2) || 'N/A'}</td>
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${student.status === 'active' ? 'bg-green-100 text-green-800' :
                                                student.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
                                                    'bg-blue-100 text-blue-800'
                                                }`}>
                                                {student.status}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4">
                                            <button
                                                onClick={() => handleDelete(student.student_id)}
                                                className="text-red-600 hover:text-red-800 text-sm font-medium"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                        <p className="text-sm text-gray-600">
                            Showing {students.length} of {total} students
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            <span className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg font-medium">
                                {page} / {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>

            {/* Import Result Modal */}
            {importResult && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">
                            {importResult.created_count === importResult.total_rows ? '✅' : '⚠️'} Import Complete
                        </h2>
                        <div className="flex gap-4 mb-4">
                            <div className="flex-1 bg-green-50 border border-green-200 rounded-xl p-4 text-center">
                                <p className="text-3xl font-bold text-green-600">{importResult.created_count}</p>
                                <p className="text-sm text-green-700 mt-1">Students Created</p>
                            </div>
                            <div className="flex-1 bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
                                <p className="text-3xl font-bold text-gray-600">{importResult.total_rows}</p>
                                <p className="text-sm text-gray-700 mt-1">Total Rows</p>
                            </div>
                            {importResult.errors.length > 0 && (
                                <div className="flex-1 bg-red-50 border border-red-200 rounded-xl p-4 text-center">
                                    <p className="text-3xl font-bold text-red-600">{importResult.errors.length}</p>
                                    <p className="text-sm text-red-700 mt-1">Errors</p>
                                </div>
                            )}
                        </div>
                        {importResult.errors.length > 0 && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 max-h-40 overflow-y-auto">
                                <p className="text-sm font-semibold text-red-700 mb-2">Errors:</p>
                                {importResult.errors.map((err, i) => (
                                    <p key={i} className="text-xs text-red-600 mb-1">• {err}</p>
                                ))}
                            </div>
                        )}
                        <button
                            onClick={() => setImportResult(null)}
                            className="w-full px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition font-semibold"
                        >
                            Done
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}
