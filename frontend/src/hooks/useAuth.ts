import { useState, useEffect, useCallback } from 'react'
import type { User } from '@/types/lobby'

const API_URL = '/api'

interface UseAuthReturn {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      console.log('useAuth: Refreshing user...')
      const res = await fetch(`${API_URL}/auth/me`, {
        credentials: 'include'
      })
      
      console.log('useAuth: Response status:', res.status)
      
      if (!res.ok) {
        console.log('useAuth: User not authenticated')
        setUser(null)
        return
      }
      
      const data = await res.json()
      console.log('useAuth: User data:', data)
      setUser(data)
    } catch (err) {
      console.error('useAuth: Error fetching user:', err)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
    } catch (err) {
      console.error('Error logging out:', err)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    logout,
    refreshUser
  }
}
