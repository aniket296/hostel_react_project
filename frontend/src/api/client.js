import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const client = axios.create({
  baseURL,
  withCredentials: true,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config || {}
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = await axios.post(`${baseURL}/auth/refresh/`, {}, { withCredentials: true })
        localStorage.setItem('access_token', refresh.data.access)
        original.headers = original.headers || {}
        original.headers.Authorization = `Bearer ${refresh.data.access}`
        return client(original)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }
    throw error
  }
)

export default client
