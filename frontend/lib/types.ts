export interface Student {
    id: string
    student_id: string
    first_name: string
    last_name: string
    email: string
    department: string
    year: number
    enrollment_date: string
    status: 'active' | 'inactive' | 'graduated'
    gpa?: number
    contact_number?: string
    address?: string
    courses: string[]
    created_at: string
    updated_at: string
}

export interface User {
    id: string
    username: string
    email: string
    role: 'admin' | 'super_admin'
    is_active: boolean
    created_at: string
    last_login?: string
}

export interface Event {
    id: string
    title: string
    description?: string
    start_date: string
    end_date: string
    category: string
    created_by: string
    created_at: string
    updated_at: string
}

export interface ChatMessage {
    message: string
    response: string
    action_taken?: {
        action: string
        [key: string]: any
    }
    timestamp?: string
}

export interface AnalyticsOverview {
    total_students: number
    active_students: number
    inactive_students: number
    graduated_students: number
    average_gpa: number
    recent_enrollments: number
}
