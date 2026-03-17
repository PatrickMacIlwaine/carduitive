import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface CountdownOverlayProps {
  count: number | null
  onComplete?: () => void
}

export function CountdownOverlay({ count, onComplete }: CountdownOverlayProps) {
  const [displayCount, setDisplayCount] = useState<number | null>(null)
  const [showGo, setShowGo] = useState(false)

  useEffect(() => {
    if (count === null) {
      setDisplayCount(null)
      setShowGo(false)
      return
    }

    setDisplayCount(count)
    
    if (count === 0) {
      setShowGo(true)
      const timer = setTimeout(() => {
        setShowGo(false)
        onComplete?.()
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [count, onComplete])

  if (displayCount === null && !showGo) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-sm">
      <AnimatePresence mode="wait">
        {showGo ? (
          <motion.div
            key="go"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center"
          >
            <div className="text-8xl md:text-9xl font-bold text-primary">
              GO!
            </div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-4 text-2xl text-muted-foreground"
            >
              Game Starting...
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key={displayCount}
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.5, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center"
          >
            <div className="text-8xl md:text-9xl font-bold text-primary">
              {displayCount}
            </div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-4 text-2xl text-muted-foreground"
            >
              Get Ready...
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
