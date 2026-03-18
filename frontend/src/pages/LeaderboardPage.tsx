import { useState, useEffect } from 'react'
import { Trophy, Medal, Award, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { API_URL } from '@/contexts/AuthContext'

interface LeaderboardEntry {
  id: number
  group_name: string
  score: number
  games_played: number
  updated_at: string
}

interface LeaderboardStats {
  total_teams: number
  high_score: number
  games_today: number
}

function RankIcon({ rank }: { rank: number }) {
  if (rank === 1) {
    return <Medal className="w-6 h-6 text-yellow-500" />
  }
  if (rank === 2) {
    return <Medal className="w-6 h-6 text-slate-400" />
  }
  if (rank === 3) {
    return <Medal className="w-6 h-6 text-amber-600" />
  }
  return <span className="w-6 h-6 flex items-center justify-center font-semibold text-muted-foreground">{rank}</span>
}

function LeaderboardRow({ entry, rank, isTopThree }: { entry: LeaderboardEntry; rank: number; isTopThree: boolean }) {
  return (
    <div
      className={cn(
        'flex items-center gap-4 p-4 rounded-lg transition-colors',
        isTopThree
          ? 'bg-primary/5 border border-primary/20'
          : 'hover:bg-muted/50'
      )}
    >
      <div className="flex-shrink-0 w-10 flex justify-center">
        <RankIcon rank={rank} />
      </div>
      
      <div className="flex-grow min-w-0">
        <p className={cn(
          'font-semibold truncate',
          isTopThree && 'text-primary'
        )}>
          {entry.group_name}
        </p>
        <p className="text-sm text-muted-foreground">
          {entry.games_played} games played
        </p>
      </div>

      <div className="flex-shrink-0 text-right">
        <p className="font-bold text-lg">{entry.score.toLocaleString()}</p>
        <p className="text-xs text-muted-foreground">points</p>
      </div>
    </div>
  )
}

export function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [stats, setStats] = useState<LeaderboardStats>({ total_teams: 0, high_score: 0, games_today: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch leaderboard entries
        const entriesRes = await fetch(`${API_URL}/leaderboard?limit=10`)
        if (!entriesRes.ok) {
          throw new Error('Failed to fetch leaderboard')
        }
        const entriesData = await entriesRes.json()
        setEntries(entriesData)
        
        // Fetch stats
        const statsRes = await fetch(`${API_URL}/leaderboard/stats`)
        if (!statsRes.ok) {
          throw new Error('Failed to fetch stats')
        }
        const statsData = await statsRes.json()
        setStats(statsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
        console.error('Error fetching leaderboard:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchLeaderboard()
  }, [])

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p className="text-destructive">Error: {error}</p>
        <p className="text-muted-foreground mt-2">Please try again later</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary">
          <Trophy className="w-5 h-5" />
          <span className="font-semibold">Global Leaderboard</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold">Top Teams</h1>
        <p className="text-muted-foreground">
          Compete with players worldwide and climb the ranks
        </p>
      </div>

      {/* Leaderboard */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-5 h-5" />
            High Scores
          </CardTitle>
          <CardDescription>
            Rankings update in real-time as games are completed
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No scores yet. Be the first to play!
            </div>
          ) : (
            entries.map((entry, index) => (
              <LeaderboardRow
                key={entry.id}
                entry={entry}
                rank={index + 1}
                isTopThree={index < 3}
              />
            ))
          )}
        </CardContent>
      </Card>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-3xl font-bold text-primary">{stats.total_teams.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">Active Teams</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-3xl font-bold text-primary">{stats.games_today.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">Games Today</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-3xl font-bold text-primary">{stats.high_score.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">High Score</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
