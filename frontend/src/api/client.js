import axios from 'axios'
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const client = axios.create({ baseURL, withCredentials: true })
client.interceptors.request.use((config) => { const token = window.localStorage.getItem('access_token'); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
client.interceptors.response.use((r) => r, async (error) => { const original = error.config; if (error.response?.status === 401 && !original._retry) { original._retry = true; try { const res = await axios.post(baseURL + '/auth/refresh/', {}, { withCredentials: true }); window.localStorage.setItem('access_token', res.data.access); original.headers.Authorization = `Bearer ${res.data.access}`; return client(original) } catch (_) { window.localStorage.removeItem('access_token'); window.localStorage.removeItem('user') } } throw error })
export default client
