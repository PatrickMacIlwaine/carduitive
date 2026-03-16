import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { useEffect, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/HomePage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'
import { LobbyPage } from '@/pages/LobbyPage'

// Component that triggers auth refresh when page becomes visible
function AuthRefresher({ children }: { children: React.ReactNode }) {
  const { refreshUser } = useAuth()
  const hasCheckedRef = useRef(false)
  
  useEffect(() => {
    // Always refresh on initial mount
    if (!hasCheckedRef.current) {
      refreshUser()
      hasCheckedRef.current = true
    }
    
    // Refresh auth state when page becomes visible (e.g., after OAuth redirect)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        refreshUser()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [refreshUser])
  
  return <>{children}</>
}

// Router definition
const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Navigate to="/home" replace /> },
      { path: 'home', element: <AuthRefresher><HomePage /></AuthRefresher> },
      { path: 'leaderboard', element: <LeaderboardPage /> },
      { path: 'lobby/:lobbyCode', element: <AuthRefresher><LobbyPage /></AuthRefresher> },
    ],
  },
])

// App wrapper with AuthProvider
function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}

export default App
