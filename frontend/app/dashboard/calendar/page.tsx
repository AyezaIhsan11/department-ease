'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import { Event } from '@/lib/types'

export default function CalendarPage() {
    const router = useRouter()
    const [events, setEvents] = useState<Event[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadEvents()
    }, [])

    const loadEvents = async () => {
        try {
            const response = await api.get('/api/events')
            setEvents(response.data)
        } catch (error) {
            console.error('Error loading events:', error)
        } finally {
            setLoading(false)
        }
    }

    const calendarEvents = events.map(event => ({
        id: event.id,
        title: event.title,
        start: event.start_date,
        end: event.end_date,
        backgroundColor: event.category === 'examination' ? '#ef4444' :
            event.category === 'academic' ? '#3b82f6' :
                event.category === 'holiday' ? '#10b981' :
                    '#8b5cf6'
    }))

    return (
        <div className="min-h-screen p-6">
            {/* Header */}
            <div className="glass-card-white mb-6 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gradient">Event Calendar</h1>
                        <p className="text-gray-600 mt-1">Department events and schedules</p>
                    </div>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                    >
                        ← Back to Dashboard
                    </button>
                </div>
            </div>

            {/* Calendar */}
            <div className="glass-card-white p-6">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                ) : (
                    <FullCalendar
                        plugins={[dayGridPlugin, interactionPlugin]}
                        initialView="dayGridMonth"
                        events={calendarEvents}
                        headerToolbar={{
                            left: 'prev,next today',
                            center: 'title',
                            right: 'dayGridMonth,dayGridWeek'
                        }}
                        height="auto"
                        eventTimeFormat={{
                            hour: 'numeric',
                            minute: '2-digit',
                            meridiem: 'short'
                        }}
                        eventDisplay="block"
                        eventClassNames="p-1 rounded-md shadow-sm border-0 font-medium text-xs cursor-pointer hover:scale-105 transition-transform"
                        eventClick={(info) => {
                            const event = events.find(e => e.id === info.event.id);
                            if (event) {
                                alert(`${event.title}\n\nTime: ${new Date(event.start_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${new Date(event.end_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}\nCategory: ${event.category}\n\n${event.description || ''}`);
                            }
                        }}
                    />
                )}
            </div>

            {/* Legend */}
            <div className="glass-card-white mt-6 p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Event Categories</h3>
                <div className="flex flex-wrap gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-blue-500 rounded"></div>
                        <span className="text-sm text-gray-700">Academic</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-500 rounded"></div>
                        <span className="text-sm text-gray-700">Examination</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-500 rounded"></div>
                        <span className="text-sm text-gray-700">Holiday</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-purple-500 rounded"></div>
                        <span className="text-sm text-gray-700">Other</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
