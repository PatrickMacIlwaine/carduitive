import { useState } from 'react'
import { ArrowRight, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface JoinLobbyFormProps {
  lobbyCode: string
  isNewLobby: boolean
  onJoin: (playerName: string) => Promise<boolean>
  onCreate: (playerName: string) => Promise<boolean>
  loading?: boolean
  error?: string | null
}

export function JoinLobbyForm({ 
  lobbyCode, 
  isNewLobby, 
  onJoin, 
  onCreate, 
  loading,
  error 
}: JoinLobbyFormProps) {
  const [playerName, setPlayerName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!playerName.trim() || isSubmitting) return

    setIsSubmitting(true)
    
    const success = isNewLobby 
      ? await onCreate(playerName.trim())
      : await onJoin(playerName.trim())
    
    // Reset form on failure
    if (!success) {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="max-w-md mx-auto">
      <CardHeader className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-mono text-lg tracking-widest mb-4">
          {lobbyCode}
        </div>
        <CardTitle className="text-2xl">
          {isNewLobby ? 'Create New Game' : 'Join Game'}
        </CardTitle>
        <CardDescription>
          {isNewLobby 
            ? "You'll be the host of this lobby"
            : "Enter your name to join this lobby"
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Input
            placeholder="Your name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="h-12 text-lg"
            maxLength={20}
            autoFocus
            disabled={isSubmitting || loading}
          />
          <Button 
            type="submit" 
            className="w-full h-12 text-lg"
            disabled={!playerName.trim() || isSubmitting || loading}
          >
            {isSubmitting || loading ? (
              <>
                <Loader2 className="mr-2 w-5 h-5 animate-spin" />
                {isNewLobby ? 'Creating...' : 'Joining...'}
              </>
            ) : (
              <>
                {isNewLobby ? 'Create Lobby' : 'Join Lobby'}
                <ArrowRight className="ml-2 w-5 h-5" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
