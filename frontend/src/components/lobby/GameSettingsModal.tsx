import { X, Settings, Heart, Skull, ArrowUpAZ, Shuffle, Zap, Timer } from 'lucide-react'
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

const PRESETS: { label: string; description: string; icon: typeof Heart; config: GameConfig }[] = [
  {
    label: 'Classic',
    description: 'Forgiving, sorted, no timer',
    icon: Heart,
    config: { failure_mode: 'forgiving', cards_sorted: true, timer_seconds: null },
  },
  {
    label: 'Hardcore',
    description: 'Back to Level 1 on failure',
    icon: Skull,
    config: { failure_mode: 'hardcore', cards_sorted: true, timer_seconds: null },
  },
  {
    label: 'Speed Hardcore',
    description: 'Hardcore + 15s timer per level',
    icon: Zap,
    config: { failure_mode: 'hardcore', cards_sorted: true, timer_seconds: 15 },
  },
]

function configMatchesPreset(config: GameConfig, preset: GameConfig): boolean {
  return (
    (config.failure_mode ?? 'forgiving') === (preset.failure_mode ?? 'forgiving') &&
    (config.cards_sorted ?? true) === (preset.cards_sorted ?? true) &&
    (config.timer_seconds ?? null) === (preset.timer_seconds ?? null)
  )
}

export function GameSettingsModal({ isOpen, onClose, config, onConfigChange, isHost }: GameSettingsModalProps) {
  if (!isOpen) return null

  const failureMode = config.failure_mode ?? 'forgiving'
  const cardsSorted = config.cards_sorted ?? true
  const timerSeconds = config.timer_seconds ?? null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md mx-4 max-h-[90vh] overflow-auto">
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
          {/* Presets */}
          <div>
            <label className="text-sm font-medium mb-2 block">Game Mode</label>
            <div className="grid grid-cols-3 gap-2">
              {PRESETS.map((preset) => {
                const Icon = preset.icon
                const isActive = configMatchesPreset(config, preset.config)
                return (
                  <button
                    key={preset.label}
                    disabled={!isHost}
                    onClick={() => onConfigChange(preset.config)}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 transition-colors ${
                      isActive
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-muted hover:border-muted-foreground/30'
                    } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium text-xs">{preset.label}</span>
                    <span className="text-[10px] text-muted-foreground text-center leading-tight">{preset.description}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Timer */}
          <div>
            <label className="text-sm font-medium mb-2 block">Timer</label>
            <div className="grid grid-cols-4 gap-2">
              {([null, 5, 10, 15] as const).map((value) => (
                <button
                  key={String(value)}
                  disabled={!isHost}
                  onClick={() => onConfigChange({ timer_seconds: value })}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-colors ${
                    timerSeconds === value
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-muted hover:border-muted-foreground/30'
                  } ${!isHost ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <Timer className="w-5 h-5" />
                  <span className="font-medium text-xs">{value === null ? 'Off' : `${value}s`}</span>
                </button>
              ))}
            </div>
          </div>

          {/* On Failure */}
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

          {/* Card Order */}
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
