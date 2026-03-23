import { motion } from 'framer-motion'
import { Trophy } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface PlayHistoryEntry {
  player_id: string
  player_name: string
  card: number
}

interface FailureInfo {
  player_id: string
  player_name: string
  card_played: number
  card_expected: number
}

interface GameResultsProps {
  gameState: {
    status: 'success' | 'failed'
    level: number
    player_hands: {
      [playerId: string]: {
        card_count: number
        cards_played: number[]
        cards?: number[]
      }
    }
    my_hand?: {
      cards: number[]
      cards_played: number[]
    }
    progression?: {
      available_actions: string[]
      message: string
      restart_level?: number
      play_history?: PlayHistoryEntry[]
      failure?: FailureInfo
    }
    leaderboard?: {
      saved: boolean
      is_new_high: boolean
      score: number
      group_name: string
    }
  }
  players: Array<{
    id: string
    name: string
    is_host?: boolean
  }>
  currentPlayerId: string
  onAdvance: () => void
  onRestart: () => void
}

function TimelineCard({ value, playerName, isYou, variant = 'default', delay = 0 }: {
  value: number
  playerName: string
  isYou: boolean
  variant?: 'default' | 'error' | 'expected'
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      className="flex flex-col items-center gap-1"
    >
      <div
        className={cn(
          "w-11 h-16 rounded-lg border-2 flex items-center justify-center text-base font-bold shadow-sm",
          variant === 'default' && "bg-slate-200 dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200",
          variant === 'error' && "bg-red-100 dark:bg-red-950 border-red-400 dark:border-red-700 text-red-700 dark:text-red-400",
          variant === 'expected' && "bg-green-100 dark:bg-green-950 border-green-400 dark:border-green-700 text-green-700 dark:text-green-400"
        )}
      >
        {value}
      </div>
      <span className={cn(
        "text-[10px] truncate max-w-[3.5rem] text-center",
        isYou ? "text-primary font-medium" : "text-muted-foreground"
      )}>
        {isYou ? 'You' : playerName}
      </span>
    </motion.div>
  )
}

function TimelineArrow({ delay = 0 }: { delay?: number }) {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay }}
      className="text-muted-foreground text-xs self-start mt-5"
    >
      →
    </motion.span>
  )
}

export function GameResults({
  gameState,
  players,
  currentPlayerId,
  onAdvance,
  onRestart
}: GameResultsProps) {
  const { status, level, player_hands, my_hand, progression, leaderboard } = gameState
  const isWin = status === 'success'
  const failure = progression?.failure
  const playHistory = progression?.play_history ?? []
  const restartLevel = progression?.restart_level ?? level

  // On failure: collect remaining cards per player for display after the timeline
  const remainingByPlayer: { name: string; isYou: boolean; cards: number[] }[] = []
  if (!isWin) {
    for (const player of players) {
      const handInfo = player_hands[player.id]
      if (!handInfo) continue
      const isYou = player.id === currentPlayerId
      const cards = isYou && my_hand ? my_hand.cards : (handInfo.cards ?? [])
      if (cards.length > 0) {
        remainingByPlayer.push({ name: player.name, isYou, cards })
      }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="absolute inset-0 bg-background/95 flex items-center justify-center z-20 p-4"
    >
      <Card className="w-full max-w-2xl max-h-[80vh] overflow-auto">
        <CardHeader className="text-center pb-3">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", bounce: 0.5 }}
          >
            <CardTitle className={cn(
              "text-4xl mb-2",
              isWin ? "text-green-500" : "text-red-500"
            )}>
              {isWin ? '🎉 Level Complete!' : '💥 Level Failed'}
            </CardTitle>
            <p className="text-muted-foreground">Level {level}</p>
          </motion.div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* What went wrong (failed only) */}
          {!isWin && failure && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 p-4"
            >
              <p className="font-medium text-red-700 dark:text-red-400 mb-2">
                {failure.player_id === currentPlayerId ? 'You' : failure.player_name} played{' '}
                <span className="font-bold">{failure.card_played}</span> — should have been{' '}
                <span className="font-bold">{failure.card_expected}</span>
              </p>
              <p className="text-sm text-muted-foreground">
                {failure.card_expected} was held by{' '}
                {/* Find who held the expected card */}
                {(() => {
                  for (const player of players) {
                    const hand = player_hands[player.id]
                    if (hand?.cards?.includes(failure.card_expected)) {
                      return player.id === currentPlayerId ? 'you' : player.name
                    }
                  }
                  return 'another player'
                })()}
              </p>
            </motion.div>
          )}

          {/* Timeline */}
          {playHistory.length > 0 && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-3">
                {isWin ? 'Play order' : 'Play history'}
              </p>
              <div className="flex flex-wrap items-start gap-1.5">
                {playHistory.map((play, idx) => (
                  <div key={idx} className="flex items-start gap-1.5">
                    {idx > 0 && <TimelineArrow delay={idx * 0.04} />}
                    <TimelineCard
                      value={play.card}
                      playerName={play.player_name}
                      isYou={play.player_id === currentPlayerId}
                      delay={idx * 0.04}
                    />
                  </div>
                ))}
                {/* Failed card at the end */}
                {failure && (
                  <div className="flex items-start gap-1.5">
                    {playHistory.length > 0 && <TimelineArrow delay={playHistory.length * 0.04} />}
                    <TimelineCard
                      value={failure.card_played}
                      playerName={failure.player_name}
                      isYou={failure.player_id === currentPlayerId}
                      variant="error"
                      delay={playHistory.length * 0.04}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Remaining cards on failure */}
          {!isWin && remainingByPlayer.length > 0 && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Cards remaining</p>
              <div className="flex flex-wrap gap-4">
                {remainingByPlayer.map((entry, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className={cn(
                      "text-sm",
                      entry.isYou ? "text-primary font-medium" : "text-muted-foreground"
                    )}>
                      {entry.isYou ? 'You' : entry.name}:
                    </span>
                    <div className="flex gap-1">
                      {entry.cards.map((card, ci) => (
                        <div
                          key={ci}
                          className="w-9 h-13 rounded border-2 bg-white dark:bg-slate-800 border-primary/30 flex items-center justify-center text-sm font-bold text-primary"
                        >
                          {card}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Leaderboard score saved */}
          {leaderboard?.saved && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "rounded-lg border p-4 text-center",
                leaderboard.is_new_high
                  ? "bg-yellow-50 dark:bg-yellow-950/30 border-yellow-300 dark:border-yellow-800"
                  : "bg-primary/5 border-primary/20"
              )}
            >
              <div className="flex items-center justify-center gap-2 mb-1">
                <Trophy className={cn("w-5 h-5", leaderboard.is_new_high ? "text-yellow-500" : "text-primary")} />
                <span className="font-semibold">
                  {leaderboard.is_new_high ? 'New High Score!' : 'Score Saved'}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Level {leaderboard.score} — {leaderboard.group_name}
              </p>
            </motion.div>
          )}

          {/* Actions */}
          <div className="flex justify-center gap-4 pt-4 border-t">
            {isWin ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onAdvance}
                className="px-8 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium shadow-lg"
              >
                Advance to Level {level + 1}
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onRestart}
                className="px-8 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium shadow-lg"
              >
                {restartLevel === level
                  ? `Try Level ${level} Again`
                  : `Back to Level ${restartLevel}`}
              </motion.button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
