import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000, // 2 min for OCR+LLM pipeline
})

api.interceptors.response.use(
  r => r,
  err => {
    console.error('[FraudRAG API]', err.response?.status, err.config?.url)
    return Promise.reject(err)
  }
)

export default api
