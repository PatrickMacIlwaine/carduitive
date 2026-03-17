import { Link, useNavigate } from 'react-router-dom'
import { Trophy, Users, Zap, Plus } from 'lucide-react'
import { LobbyCodeInput } from '@/components/lobby/LobbyCodeInput'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

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

  const handleNewGame = () => {
    const lobbyCode = generateLobbyCode()
    navigate(`/lobby/${lobbyCode}`)
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
