import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { API_URL } from '@/contexts/AuthContext'

export function LobbyCodeInput() {
  const [lobbyCode, setLobbyCode] = useState('')
  const [error, setError] = useState('')
  const [isChecking, setIsChecking] = useState(false)
  const navigate = useNavigate()

  const validateCode = (code: string): boolean => {
    const regex = /^[A-Z]{5}$/
    return regex.test(code)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase()
    // Only allow letters, max 5 characters
    const filtered = value.replace(/[^A-Z]/g, '').slice(0, 5)
    setLobbyCode(filtered)
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!lobbyCode) {
      setError('Please enter a lobby code')
      return
    }

    if (!validateCode(lobbyCode)) {
      setError('Lobby code must be exactly 5 letters (A-Z)')
      return
    }

    // Check if lobby exists before navigating
    setIsChecking(true)
    try {
      const res = await fetch(`${API_URL}/lobbies/${lobbyCode}`, {
        credentials: 'include'
      })
      
      if (res.status === 404) {
        setError('Lobby not found')
        return
      }

      if (!res.ok) {
        setError('Unable to check lobby. Please try again.')
        return
      }

      // Lobby exists, navigate to it
      navigate(`/lobby/${lobbyCode}`)
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Join a Game</CardTitle>
        <CardDescription>
          Enter a 5-letter lobby code to join your friends
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Input
              type="text"
              placeholder="ABCDE"
              value={lobbyCode}
              onChange={handleInputChange}
              className="text-center text-2xl tracking-widest uppercase h-14 font-mono"
              maxLength={5}
              autoComplete="off"
              autoFocus
              disabled={isChecking}
            />
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
          <Button 
            type="submit" 
            className="w-full h-12 text-lg"
            disabled={lobbyCode.length !== 5 || isChecking}
          >
            {isChecking ? (
              <span>Checking...</span>
            ) : (
              <>
                Join Lobby
                <ArrowRight className="ml-2 w-5 h-5" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
