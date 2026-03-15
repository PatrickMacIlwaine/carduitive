import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/HomePage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'
import { LobbyPage } from '@/pages/LobbyPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Navigate to="/home" replace /> },
      { path: 'home', element: <HomePage /> },
      { path: 'leaderboard', element: <LeaderboardPage /> },
      { path: 'lobby/:lobbyCode', element: <LobbyPage /> },
    ],
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
