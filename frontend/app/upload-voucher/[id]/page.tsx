'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import axios from 'axios'
import { API_URL } from '@/lib/api'

export default function UploadVoucherPage() {
    const params = useParams()
    const studentId = params.id as string
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [uploading, setUploading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0]
        if (selectedFile) {
            setFile(selectedFile)
            const reader = new FileReader()
            reader.onloadend = () => {
                setPreview(reader.result as string)
            }
            reader.readAsDataURL(selectedFile)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!file) return

        setUploading(true)
        setMessage(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            await axios.post(`${API_URL}/api/vouchers/upload/${studentId}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            setMessage({ type: 'success', text: 'Voucher uploaded successfully! You can close this page.' })
            setFile(null)
            setPreview(null)
        } catch (error: any) {
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to upload voucher. Please try again.' })
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
            <div className="max-w-md w-full glass-card-white p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gradient">Upload Fee Voucher</h1>
                    <p className="text-gray-600 mt-2">Student ID: <span className="font-mono font-bold text-blue-600">{studentId}</span></p>
                </div>

                {message && (
                    <div className={`mb-6 p-4 rounded-lg text-center ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {message.text}
                    </div>
                )}

                {message?.type !== 'success' && (
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-blue-400 transition cursor-pointer relative">
                            <input
                                type="file"
                                onChange={handleFileChange}
                                accept="image/*,application/pdf"
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                required
                            />
                            {preview ? (
                                <img src={preview} alt="Preview" className="max-h-64 rounded-lg" />
                            ) : (
                                <div className="text-center">
                                    <span className="text-4xl mb-2 block">📸</span>
                                    <p className="text-gray-600 font-medium">Click or drag photo here</p>
                                    <p className="text-xs text-gray-400 mt-1">PNG, JPG or PDF up to 10MB</p>
                                </div>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={!file || uploading}
                            className={`w-full py-4 rounded-xl font-bold text-white shadow-lg transition ${
                                !file || uploading 
                                ? 'bg-gray-400 cursor-not-allowed' 
                                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:shadow-xl'
                            }`}
                        >
                            {uploading ? 'Uploading...' : 'Submit Voucher'}
                        </button>
                    </form>
                )}
                
                <p className="text-center text-xs text-gray-400 mt-8">
                    Department Administration System &copy; 2024
                </p>
            </div>
        </div>
    )
}
