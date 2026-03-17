import { AlertTriangle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

interface NavigationWarningModalProps {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function NavigationWarningModal({ isOpen, onConfirm, onCancel }: NavigationWarningModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-md mx-4 shadow-2xl">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-2 text-amber-500 mb-2">
            <AlertTriangle className="w-6 h-6" />
            <CardTitle className="text-lg">Leave Lobby?</CardTitle>
          </div>
          <CardDescription className="text-base">
            You are currently in an active game lobby. If you leave, you will exit the game and lose your progress.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="py-4 px-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-sm text-amber-800 dark:text-amber-200">
              <strong>Warning:</strong> Leaving will disconnect you from the game. 
              Other players will see you as offline.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              onClick={onCancel}
              className="flex-1"
            >
              <X className="w-4 h-4 mr-2" />
              Stay in Lobby
            </Button>
            <Button
              variant="destructive"
              onClick={onConfirm}
              className="flex-1"
            >
              Leave Anyway
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
