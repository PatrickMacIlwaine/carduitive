import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/HomePage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'
import { LobbyPage } from '@/pages/LobbyPage'

function AuthRefresher({ children }: { children: React.ReactNode }) {
  const [refreshKey, setRefreshKey] = useState(0)
  
  useEffect(() => {
    // Refresh auth state when page becomes visible (e.g., after OAuth redirect)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        setRefreshKey(k => k + 1)
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [])
  
  return <div key={refreshKey}>{children}</div>
}

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

function App() {
  return <RouterProvider router={router} />
}

export default App
