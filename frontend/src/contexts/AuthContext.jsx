import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchUser = async () => {
    try {
      const userData = await api.get('/api/v1/auth/me', token)
      setUser(userData)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    const response = await api.post('/api/v1/auth/login', { username: email, password })
    localStorage.setItem('token', response.access_token)
    setToken(response.access_token)
    setUser(response.user)
    return response.user
  }

  const register = async (email, password, username, fullName) => {
    const response = await api.post('/api/v1/auth/register', {
      email,
      password,
      username,
      full_name: fullName
    })
    localStorage.setItem('token', response.access_token)
    setToken(response.access_token)
    setUser(response.user)
    return response.user
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
