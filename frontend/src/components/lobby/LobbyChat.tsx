import { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { ChatMessage } from '@/types/lobby'

interface LobbyChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  disabled?: boolean
}

function ChatMessageItem({ message }: { message: ChatMessage }) {
  const isSystem = message.type === 'system'
  const isCurrentUser = message.player_id !== 'system' && !isSystem

  if (isSystem) {
    return (
      <div className="flex justify-center py-2">
        <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {message.message}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex gap-2 py-1 ${isCurrentUser ? 'flex-row-reverse' : ''}`}>
      <div className="flex-1 min-w-0">
        <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'}`}>
          <span className="text-xs text-muted-foreground mb-1">
            {message.player_name}
          </span>
          <div className={`px-3 py-2 rounded-lg max-w-[85%] break-words ${
            isCurrentUser 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted'
          }`}>
            <p className="text-sm">{message.message}</p>
          </div>
          <span className="text-[10px] text-muted-foreground mt-1">
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        </div>
      </div>
    </div>
  )
}

export function LobbyChat({ messages, onSendMessage, disabled }: LobbyChatProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || disabled) return

    onSendMessage(input.trim())
    setInput('')
    
    // Refocus input after sending
    setTimeout(() => {
      inputRef.current?.focus()
    }, 0)
  }

  return (
    <Card className="flex flex-col h-[400px]">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Lobby Chat
        </CardTitle>
        <CardDescription>
          Chat with other players in the lobby
        </CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-1 pr-2 -mr-2 mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No messages yet.</p>
              <p className="text-xs">Start the conversation!</p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessageItem key={message.id} message={message} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0">
          <Input
            ref={inputRef}
            placeholder={disabled ? "Connecting..." : "Type a message..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={disabled}
            className="flex-1"
            maxLength={200}
          />
          <Button 
            type="submit" 
            size="icon"
            disabled={disabled || !input.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
