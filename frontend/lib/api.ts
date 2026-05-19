import axios from 'axios'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token')
            if (token) {
                config.headers.Authorization = `Bearer ${token}`
            }
        }
        // Let axios set Content-Type automatically for FormData (includes boundary)
        if (config.data instanceof FormData) {
            delete config.headers['Content-Type']
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            if (typeof window !== 'undefined') {
                const refreshToken = localStorage.getItem('refresh_token')

                if (refreshToken) {
                    try {
                        const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                            refresh_token: refreshToken
                        })

                        const { access_token, refresh_token: newRefreshToken } = response.data

                        localStorage.setItem('access_token', access_token)
                        localStorage.setItem('refresh_token', newRefreshToken)

                        originalRequest.headers.Authorization = `Bearer ${access_token}`
                        return api(originalRequest)
                    } catch (refreshError) {
                        // Refresh failed, logout user
                        localStorage.removeItem('access_token')
                        localStorage.removeItem('refresh_token')
                        window.location.href = '/login'
                        return Promise.reject(refreshError)
                    }
                } else {
                    // No refresh token, logout
                    window.location.href = '/login'
                }
            }
        }

        return Promise.reject(error)
    }
)

export default api
