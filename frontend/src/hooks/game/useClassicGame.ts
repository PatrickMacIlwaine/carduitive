import { useCallback } from 'react'

const CLASSIC_DEFAULT_CONFIG = {
  deck_size: 100,
  timing_mode: 'relaxed',
}

interface UseClassicGameReturn {
  startGame: () => Promise<boolean>
  playCard: (card: number) => Promise<boolean>
  advanceLevel: () => Promise<boolean>
  restartLevel: () => Promise<boolean>
}

export function useClassicGame(
  sendGameAction: (action: string, data?: Record<string, unknown>) => Promise<boolean>,
  startLobbyGame: (gameType: string, config: Record<string, unknown>) => Promise<boolean>
): UseClassicGameReturn {
  const startGame = useCallback(
    () => startLobbyGame('classic', CLASSIC_DEFAULT_CONFIG),
    [startLobbyGame]
  )

  const playCard = useCallback(
    (card: number) => sendGameAction('play', { card }),
    [sendGameAction]
  )

  const advanceLevel = useCallback(
    () => sendGameAction('advance'),
    [sendGameAction]
  )

  const restartLevel = useCallback(
    () => sendGameAction('restart'),
    [sendGameAction]
  )

  return { startGame, playCard, advanceLevel, restartLevel }
}
