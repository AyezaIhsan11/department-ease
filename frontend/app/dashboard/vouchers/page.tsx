'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api, { API_URL } from '@/lib/api'

interface Voucher {
    id: string
    student_id: string
    student_name: string
    filename: string
    file_path: string
    upload_date: string
    status: string
}

export default function VouchersPage() {
    const router = useRouter()
    const [vouchers, setVouchers] = useState<Voucher[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('access_token')
        if (!token) {
            router.push('/login')
            return
        }
        loadVouchers()
    }, [])

    const loadVouchers = async () => {
        try {
            const res = await api.get('/api/vouchers')
            setVouchers(res.data)
        } catch (error) {
            console.error('Error loading vouchers:', error)
        } finally {
            setLoading(false)
        }
    }

    const updateStatus = async (id: string, status: string) => {
        try {
            await api.patch(`/api/vouchers/${id}/status?status=${status}`)
            loadVouchers()
        } catch (error) {
            console.error('Error updating status:', error)
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-900">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-white"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen p-6 bg-slate-900">
            <div className="glass-card-white mb-6 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gradient">Fee Vouchers</h1>
                    <p className="text-gray-600 mt-1">Review and verify student fee submissions</p>
                </div>
                <button
                    onClick={() => router.push('/dashboard')}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition w-full sm:w-auto text-center"
                >
                    Back to Dashboard
                </button>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {vouchers.map((voucher) => (
                    <div key={voucher.id} className="glass-card-white overflow-hidden flex flex-col">
                        <div className="h-48 bg-gray-100 relative">
                            {voucher.file_path.endsWith('.pdf') ? (
                                <div className="flex items-center justify-center h-full text-4xl">📄</div>
                            ) : (
                                <img 
                                    src={`${API_URL}${voucher.file_path}`} 
                                    alt="Voucher" 
                                    className="w-full h-full object-cover"
                                />
                            )}
                            <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold uppercase ${
                                voucher.status === 'verified' ? 'bg-green-500 text-white' : 
                                voucher.status === 'rejected' ? 'bg-red-500 text-white' : 'bg-yellow-500 text-white'
                            }`}>
                                {voucher.status}
                            </div>
                        </div>
                        <div className="p-4 flex-grow">
                            <h3 className="font-bold text-lg text-gray-900">{voucher.student_name}</h3>
                            <p className="text-sm text-blue-600 font-mono">{voucher.student_id}</p>
                            <p className="text-xs text-gray-400 mt-2">
                                Uploaded: {new Date(voucher.upload_date).toLocaleString()}
                            </p>
                        </div>
                        <div className="p-4 border-t border-gray-100 flex gap-2">
                            <a 
                                href={`${API_URL}${voucher.file_path}`} 
                                target="_blank"
                                className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 rounded text-sm font-semibold text-center hover:bg-blue-100 transition"
                            >
                                View Full
                            </a>
                            {voucher.status === 'pending' && (
                                <>
                                    <button 
                                        onClick={() => updateStatus(voucher.id, 'verified')}
                                        className="px-3 py-2 bg-green-500 text-white rounded text-sm font-semibold hover:bg-green-600 transition"
                                    >
                                        Verify
                                    </button>
                                    <button 
                                        onClick={() => updateStatus(voucher.id, 'rejected')}
                                        className="px-3 py-2 bg-red-500 text-white rounded text-sm font-semibold hover:bg-red-600 transition"
                                    >
                                        Reject
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                ))}

                {vouchers.length === 0 && (
                    <div className="col-span-full py-12 text-center text-gray-500 glass-card-white">
                        <span className="text-4xl block mb-2">📁</span>
                        No vouchers have been uploaded yet.
                    </div>
                )}
            </div>
        </div>
    )
}
