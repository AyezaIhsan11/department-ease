'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { ChatMessage } from '@/lib/types'

export default function ChatPage() {
    const router = useRouter()
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [conversationId, setConversationId] = useState<string | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    useEffect(() => {
        // Check authentication
        const token = localStorage.getItem('access_token')
        if (!token) {
            router.push('/login')
        }
    }, [router])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!input.trim()) return

        const userMessage = input.trim()
        setInput('')
        setLoading(true)

        // Add user message to chat
        const newMessage: ChatMessage = {
            message: userMessage,
            response: '',
        }
        setMessages(prev => [...prev, newMessage])

        try {
            const response = await api.post('/api/chat', {
                message: userMessage,
                conversation_id: conversationId,
            })

            const { response: aiResponse, conversation_id, action_taken } = response.data

            // Update conversation ID
            if (!conversationId) {
                setConversationId(conversation_id)
            }

            // Update message with response
            setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                    message: userMessage,
                    response: aiResponse,
                    action_taken,
                }
                return updated
            })
        } catch (err: any) {
            setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                    message: userMessage,
                    response: err.response?.data?.detail || 'Sorry, I encountered an error. Please try again.',
                }
                return updated
            })
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/login')
    }

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="glass-card m-4 p-4 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">AI Assistant</h1>
                    <p className="text-white/70 text-sm">Ask me anything about student management</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="btn-secondary"
                    >
                        Dashboard
                    </button>
                    <button
                        onClick={handleLogout}
                        className="btn-secondary"
                    >
                        Logout
                    </button>
                </div>
            </header>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto px-4 pb-4">
                <div className="max-w-4xl mx-auto space-y-4">
                    {messages.length === 0 && (
                        <div className="glass-card p-8 text-center">
                            <div className="text-5xl mb-4">🤖</div>
                            <h2 className="text-2xl font-bold text-white mb-2">
                                Welcome to AI Assistant
                            </h2>
                            <p className="text-white/70 mb-6">
                                I can help you manage student records using natural language commands
                            </p>
                            <div className="grid md:grid-cols-2 gap-4 text-left">
                                <div className="bg-white/10 rounded-lg p-4">
                                    <p className="text-white font-medium mb-1">📝 Create Students</p>
                                    <p className="text-white/60 text-sm">
                                        "Add a new student named John Doe"
                                    </p>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4">
                                    <p className="text-white font-medium mb-1">🔍 Search</p>
                                    <p className="text-white/60 text-sm">
                                        "Show me all CS students"
                                    </p>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4">
                                    <p className="text-white font-medium mb-1">✏️ Update</p>
                                    <p className="text-white/60 text-sm">
                                        "Update student CS001 GPA to 3.8"
                                    </p>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4">
                                    <p className="text-white font-medium mb-1">📊 Statistics</p>
                                    <p className="text-white/60 text-sm">
                                        "Give me student statistics"
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div key={idx} className="space-y-3">
                            {/* User Message */}
                            <div className="flex justify-end">
                                <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl rounded-tr-none px-6 py-3 max-w-xl shadow-lg">
                                    <p>{msg.message}</p>
                                </div>
                            </div>

                            {/* AI Response */}
                            {msg.response && (
                                <div className="flex justify-start">
                                    <div className="glass-card px-6 py-4 max-w-xl">
                                        <p className="text-white whitespace-pre-wrap">{msg.response}</p>
                                        {msg.action_taken && (
                                            <div className="mt-3 pt-3 border-t border-white/20">
                                                <span className="text-green-400 text-sm font-medium">
                                                    ✓ Action: {msg.action_taken.action.replace('_', ' ')}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div className="flex justify-start">
                            <div className="glass-card px-6 py-4">
                                <div className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Form */}
            <div className="p-4">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                    <div className="glass-card p-2 flex items-center gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 bg-transparent border-none text-white placeholder-white/60 focus:outline-none px-4 py-2"
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Send
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
