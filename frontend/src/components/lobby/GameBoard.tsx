import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { HelpCircle, Wifi, WifiOff, Crown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { GameResults } from './GameResults'

interface GameBoardProps {
  gameState: {
    game_type: string
    status: 'playing' | 'success' | 'failed'
    level: number
    played_cards: number[]
    next_expected: number
    player_hands: {
      [playerId: string]: {
        card_count: number
        cards_played: number[]
      }
    }
    my_hand?: {
      cards: number[]
      cards_played: number[]
    }
    progression?: {
      available_actions: string[]
      message: string
    }
  }
  currentPlayerId: string
  players: Array<{
    id: string
    name: string
    is_connected?: boolean
    is_host?: boolean
  }>
  onPlayCard: (card: number) => void
  onAdvance: () => void
  onRestart: () => void
}

export function GameBoard({ 
  gameState, 
  currentPlayerId, 
  players,
  onPlayCard,
  onAdvance,
  onRestart
}: GameBoardProps) {
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)

  const { 
    level, 
    played_cards, 
    next_expected, 
    player_hands, 
    my_hand,
    status,
    progression
  } = gameState

  // Get my cards
  const myCards = my_hand?.cards || []
  
  // Get other players (exclude current player)
  const otherPlayers = players.filter(p => p.id !== currentPlayerId)

  // Get last played card
  const lastPlayedCard = played_cards.length > 0 
    ? played_cards[played_cards.length - 1] 
    : null

  const handlePlayCard = (card: number) => {
    if (status === 'playing') {
      onPlayCard(card)
    }
  }

  return (
    <div className="w-full h-full flex flex-col relative">
      {/* Top: Level Info */}
      <div className="flex-shrink-0 py-4 px-4">
        <div className="flex justify-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary">
            <span className="font-bold text-lg">Level {level}</span>
            <span className="text-sm opacity-70">•</span>
            <span className="text-sm">Next: {next_expected}</span>
          </div>
        </div>
      </div>

      {/* Opponent Cards */}
      <div className="flex-shrink-0 py-4 px-4">
        <div className="flex justify-center items-end gap-8" style={{ perspective: '1000px' }}>
          {otherPlayers.map((player, index) => {
            const handInfo = player_hands[player.id] || { card_count: 0 }
            const cardCount = handInfo.card_count
            const totalPlayers = otherPlayers.length
            const rotation = (index - (totalPlayers - 1) / 2) * 10
            const isConnected = player.is_connected ?? true
            
            return (
              <motion.div
                key={player.id}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "relative flex flex-col items-center",
                  !isConnected && "opacity-50 grayscale"
                )}
                style={{
                  transform: `rotate(${rotation}deg)`,
                  zIndex: index
                }}
              >
                {/* Connection Status Indicator */}
                <div className={cn(
                  "absolute -top-2 -right-1 z-20 w-5 h-5 rounded-full flex items-center justify-center border-2",
                  isConnected 
                    ? "bg-green-500 border-green-600" 
                    : "bg-red-500 border-red-600"
                )}>
                  {isConnected ? (
                    <Wifi className="w-3 h-3 text-white" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-white" />
                  )}
                </div>
                
                {/* Fanned Card Backs */}
                <div className="relative" style={{ height: '6rem', width: '4rem' }}>
                  {Array.from({ length: Math.min(cardCount, 5) }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "absolute w-14 h-20 md:w-16 md:h-24 rounded-lg border-2 shadow-md",
                        isConnected 
                          ? "bg-slate-700 border-slate-600" 
                          : "bg-slate-500 border-slate-400"
                      )}
                      style={{
                        transform: `translateX(${i * 6}px) translateY(${i * -1}px) rotate(${i * 2}deg)`,
                        zIndex: i
                      }}
                    >
                      {i === Math.min(cardCount, 5) - 1 && (
                        <HelpCircle className="w-8 h-8 md:w-10 md:h-10 text-slate-400 absolute inset-0 m-auto" />
                      )}
                    </div>
                  ))}
                  {cardCount > 5 && (
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center z-30">
                      +{cardCount - 5}
                    </div>
                  )}
                </div>
                
                {/* Player Info */}
                <div className="mt-2 text-center">
                  <p className="text-xs font-medium truncate max-w-[80px]">{player.name}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {cardCount} card{cardCount !== 1 ? 's' : ''}
                  </p>
                  {!isConnected && (
                    <span className="text-[10px] text-red-500 font-medium">Offline</span>
                  )}
                  {player.is_host && (
                    <div className="flex items-center justify-center gap-0.5 text-yellow-500">
                      <Crown className="w-3 h-3" />
                      <span className="text-[10px]">Host</span>
                    </div>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Center: Game Status and Last Played */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-2">
        {/* Status Message */}
        <p className="text-sm text-muted-foreground text-center mb-6">
          {status === 'success' && progression?.message}
          {status === 'failed' && progression?.message}
        </p>

        {/* Last Played Card */}
        <div className="mb-6">
          <p className="text-sm text-muted-foreground text-center mb-3">Last Played</p>
          {lastPlayedCard ? (
            <motion.div
              key={lastPlayedCard}
              initial={{ scale: 0.8, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              className="w-28 h-40 md:w-36 md:h-52 rounded-xl bg-white border-2 border-slate-200 shadow-2xl flex items-center justify-center relative overflow-hidden"
            >
              <div className="absolute inset-0 opacity-5 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-400 to-transparent" />
              <span className="text-6xl md:text-7xl font-bold text-slate-800">
                {lastPlayedCard}
              </span>
              <span className="absolute top-3 left-3 text-lg font-bold text-slate-400">
                {lastPlayedCard}
              </span>
              <span className="absolute bottom-3 right-3 text-lg font-bold text-slate-400 rotate-180">
                {lastPlayedCard}
              </span>
            </motion.div>
          ) : (
            <div className="w-28 h-40 md:w-36 md:h-52 rounded-xl border-2 border-dashed border-slate-300 flex items-center justify-center bg-slate-50/50">
              <span className="text-slate-400 text-sm">Waiting...</span>
            </div>
          )}
        </div>

        {/* Progression Controls */}
        {status === 'success' && (
          <Button 
            size="lg" 
            onClick={onAdvance}
            className="px-8"
          >
            Advance to Level {level + 1}
          </Button>
        )}
        {status === 'failed' && (
          <Button 
            size="lg" 
            variant="destructive"
            onClick={onRestart}
            className="px-8"
          >
            Try Level {level} Again
          </Button>
        )}
      </div>

      {/* Bottom: Your Hand (Larger and Fanned) */}
      <div className="flex-shrink-0 py-6 px-4 bg-gradient-to-t from-background to-transparent">
        <h3 className="text-center text-lg font-semibold mb-4">
          Your Hand
        </h3>
        
        {status === 'playing' ? (
          <div className="flex justify-center items-end" style={{ perspective: '1000px' }}>
            {myCards.map((card, index) => {
              const isHovered = hoveredCard === card
              const totalCards = myCards.length
              const rotation = (index - (totalCards - 1) / 2) * 6
              const horizontalOffset = (index - (totalCards - 1) / 2) * 15
              
              return (
                <motion.button
                  key={card}
                  onClick={() => handlePlayCard(card)}
                  onMouseEnter={() => setHoveredCard(card)}
                  onMouseLeave={() => setHoveredCard(null)}
                  whileHover={{ 
                    y: -30, 
                    scale: 1.15,
                    zIndex: 20,
                    transition: { duration: 0.2 }
                  }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ y: 0, rotate: rotation, x: horizontalOffset }}
                  animate={{ 
                    y: isHovered ? -30 : 0,
                    rotate: isHovered ? 0 : rotation,
                    x: isHovered ? horizontalOffset * 1.2 : horizontalOffset,
                    zIndex: isHovered ? 20 : index
                  }}
                  className={`
                    relative w-24 h-36 md:w-32 md:h-44
                    rounded-xl bg-white border-2 border-slate-300 shadow-xl
                    flex items-center justify-center
                    cursor-pointer
                    hover:border-primary hover:shadow-2xl
                    transition-shadow
                  `}
                  style={{
                    marginLeft: index > 0 ? '-40px' : '0',
                    zIndex: index
                  }}
                >
                  {/* Card value */}
                  <span className="text-4xl md:text-5xl font-bold text-slate-800">
                    {card}
                  </span>
                  
                  {/* Corner decorations */}
                  <span className="absolute top-2 left-3 text-sm font-bold text-slate-400">
                    {card}
                  </span>
                  <span className="absolute bottom-2 right-3 text-sm font-bold text-slate-400 rotate-180">
                    {card}
                  </span>
                  
                  {/* Hover overlay */}
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 bg-primary/10 rounded-xl flex items-center justify-center"
                    >
                      <span className="text-primary font-bold text-lg bg-white/95 px-4 py-2 rounded-lg shadow-lg">
                        Play
                      </span>
                    </motion.div>
                  )}
                </motion.button>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-muted-foreground text-lg">
              {status === 'success' ? '🎉 Level Complete!' : '💥 Level Failed'}
            </p>
          </div>
        )}
        
        <p className="text-center text-sm text-muted-foreground mt-4">
          {myCards.length} card{myCards.length !== 1 ? 's' : ''} in hand • {played_cards.length} played
        </p>
      </div>

      {/* Game Results Overlay */}
      {(status === 'success' || status === 'failed') && (
        <GameResults
          gameState={{
            status,
            level,
            player_hands,
            my_hand
          }}
          players={players}
          currentPlayerId={currentPlayerId}
          onAdvance={onAdvance}
          onRestart={onRestart}
        />
      )}
    </div>
  )
}
