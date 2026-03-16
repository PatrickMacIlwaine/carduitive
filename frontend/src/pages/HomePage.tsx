import { Link, useNavigate } from 'react-router-dom'
import { Trophy, Users, Zap, Plus, User } from 'lucide-react'
import { LobbyCodeInput } from '@/components/lobby/LobbyCodeInput'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'

function generateLobbyCode(): string {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  let code = ''
  for (let i = 0; i < 5; i++) {
    code += letters.charAt(Math.floor(Math.random() * letters.length))
  }
  return code
}

export function HomePage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, isLoading } = useAuth()

  const handleNewGame = () => {
    const lobbyCode = generateLobbyCode()
    navigate(`/lobby/${lobbyCode}`)
  }

  const handleLogin = () => {
    window.location.href = '/api/auth/google/login?redirect=/home'
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-carduitive-dark via-carduitive-teal to-carduitive-light bg-clip-text text-transparent">
          Welcome to Carduitive
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          The intuitive card game experience. Create a new game or join friends in a lobby!
        </p>
        
        {/* User welcome or sign-in prompt */}
        {!isLoading && (
          isAuthenticated && user ? (
            <div className="flex items-center justify-center gap-3 mt-4 p-3 bg-primary/5 rounded-lg inline-flex">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.name}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-500" />
                </div>
              )}
              <div className="text-left">
                <p className="font-medium">Welcome back, {user.name}!</p>
                <p className="text-sm text-muted-foreground">Ready to play?</p>
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <Button
                variant="outline"
                onClick={handleLogin}
                className="flex items-center gap-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign in with Google to save your progress
              </Button>
            </div>
          )
        )}
      </div>

      {/* Game Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* New Game */}
        <Card className="relative overflow-hidden group cursor-pointer" onClick={handleNewGame}>
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity" />
          <CardContent className="pt-6 text-center space-y-4 relative">
            <div className="w-16 h-16 mx-auto rounded-full bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Plus className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h3 className="font-bold text-xl mb-1">New Game</h3>
              <p className="text-sm text-muted-foreground">
                Create a lobby and invite friends
              </p>
            </div>
            <Button className="w-full" size="lg">
              Create Lobby
            </Button>
          </CardContent>
        </Card>

        {/* Join Game */}
        <div className="flex flex-col justify-center">
          <LobbyCodeInput />
        </div>
      </div>

      {/* Leaderboard Link */}
      <div className="text-center">
        <Link to="/leaderboard">
          <Button variant="ghost" size="lg" className="text-muted-foreground hover:text-foreground">
            <Trophy className="mr-2 w-5 h-5" />
            View Leaderboard
          </Button>
        </Link>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-8">
        <Card>
          <CardContent className="pt-6 text-center space-y-2">
            <div className="w-12 h-12 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
              <Users className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold">Multiplayer</h3>
            <p className="text-sm text-muted-foreground">
              Play with friends in real-time lobbies
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center space-y-2">
            <div className="w-12 h-12 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
              <Zap className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold">Fast-Paced</h3>
            <p className="text-sm text-muted-foreground">
              Quick rounds with instant updates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center space-y-2">
            <div className="w-12 h-12 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
              <Trophy className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold">Competitive</h3>
            <p className="text-sm text-muted-foreground">
              Climb the global leaderboard
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
