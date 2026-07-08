// API utility for making requests to the backend

const API_BASE_URL = localStorage.getItem('API_URL') || 'http://localhost:8001'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('token')
  
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers
    }
  }

  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body)
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
    
    // Handle blob responses
    if (response.headers.get('content-type')?.includes('application/json')) {
      const data = await response.json()
      
      if (!response.ok) {
        throw new ApiError(
          data.detail || 'An error occurred',
          response.status,
          data
        )
      }
      
      return data
    }
    
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new ApiError(
        data.detail || 'An error occurred',
        response.status,
        data
      )
    }
    
    return response.blob()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(error.message, 0, null)
  }
}

export const api = {
  get: (endpoint, token = null) => request(endpoint, { method: 'GET' }),
  
  post: (endpoint, body) => request(endpoint, { method: 'POST', body }),
  
  put: (endpoint, body) => request(endpoint, { method: 'PUT', body }),
  
  delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
  
  setBaseUrl: (url) => {
    localStorage.setItem('API_URL', url)
  },
  
  getBaseUrl: () => API_BASE_URL
}

// Directors API
export const directorsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return api.get(`/api/v1/directors${query ? '?' + query : ''}`)
  },
  
  get: (id) => api.get(`/api/v1/directors/${id}`),
  
  random: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return api.get(`/api/v1/directors/random${query ? '?' + query : ''}`)
  },
  
  getLetters: () => api.get('/api/v1/directors/letters'),
  
  getGenres: () => api.get('/api/v1/directors/genres'),
  
  getMoods: () => api.get('/api/v1/directors/moods'),
  
  getCountries: () => api.get('/api/v1/directors/countries'),
  
  addFavorite: (directorId, notes = null) => api.post('/api/v1/directors/favorites', { director_id: directorId, notes }),
  
  removeFavorite: (directorId) => api.delete(`/api/v1/directors/favorites/${directorId}`),
  
  getFavorites: () => api.get('/api/v1/directors/favorites/me')
}

// Script Analysis API
export const analysisApi = {
  analyze: (data) => api.post('/api/v1/analyze', data),
  
  history: (page = 1, limit = 20) => api.get(`/api/v1/analysis/history?page=${page}&limit=${limit}`)
}

// Generation API
export const generationApi = {
  start: (data) => api.post('/api/v1/generate', data),
  
  status: (jobId) => api.get(`/api/v1/jobs/${jobId}/status`),
  
  get: (jobId) => api.get(`/api/v1/jobs/${jobId}`),
  
  cancel: (jobId) => api.delete(`/api/v1/jobs/${jobId}`),
  
  history: (page = 1, limit = 20) => api.get(`/api/v1/generations/history?page=${page}&limit=${limit}`)
}
