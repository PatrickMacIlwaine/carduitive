import { X, Settings, Heart, Skull, ArrowUpAZ, Shuffle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import type { GameConfig } from '@/types/lobby'

interface GameSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  config: GameConfig
  onConfigChange: (config: Partial<GameConfig>) => void
  isHost: boolean
}

export function GameSettingsModal({ isOpen, onClose, config, onConfigChange, isHost }: GameSettingsModalProps) {
  if (!isOpen) return null

  const failureMode = config.failure_mode ?? 'forgiving'
  const cardsSorted = config.cards_sorted ?? true

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md mx-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Game Settings
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <CardDescription>
            {isHost ? 'Configure the rules before starting' : 'Game rules set by host'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">On Failure</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                disabled={!isHost}
                onClick={() => onConfigChange({ failure_mode: 'forgiving' })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  failureMode === 'forgiving'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-muted hover:border-muted-foreground/30'
                } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <Heart className="w-6 h-6" />
                <span className="font-medium text-sm">Forgiving</span>
                <span className="text-xs text-muted-foreground text-center">Restart from the level you failed</span>
              </button>
              <button
                disabled={!isHost}
                onClick={() => onConfigChange({ failure_mode: 'hardcore' })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  failureMode === 'hardcore'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-muted hover:border-muted-foreground/30'
                } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <Skull className="w-6 h-6" />
                <span className="font-medium text-sm">Hardcore</span>
                <span className="text-xs text-muted-foreground text-center">Back to Level 1 on any failure</span>
              </button>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Card Order</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                disabled={!isHost}
                onClick={() => onConfigChange({ cards_sorted: true })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  cardsSorted
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-muted hover:border-muted-foreground/30'
                } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <ArrowUpAZ className="w-6 h-6" />
                <span className="font-medium text-sm">Sorted</span>
                <span className="text-xs text-muted-foreground text-center">Cards in your hand are sorted low to high</span>
              </button>
              <button
                disabled={!isHost}
                onClick={() => onConfigChange({ cards_sorted: false })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  !cardsSorted
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-muted hover:border-muted-foreground/30'
                } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <Shuffle className="w-6 h-6" />
                <span className="font-medium text-sm">Shuffled</span>
                <span className="text-xs text-muted-foreground text-center">Cards in your hand are in random order</span>
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
