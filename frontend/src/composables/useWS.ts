import { onUnmounted } from 'vue'

type WSHandler = (data: Record<string, unknown>) => void

const handlers: Map<string, Set<WSHandler>> = new Map()
let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function getWsUrl(): string {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws`
}

function connect() {
  if (socket && socket.readyState <= WebSocket.OPEN) return

  socket = new WebSocket(getWsUrl())

  socket.onmessage = (e) => {
    try {
      const { event, data } = JSON.parse(e.data)
      handlers.get(event)?.forEach(fn => fn(data))
      handlers.get('*')?.forEach(fn => fn({ event, ...data }))
    } catch {}
  }

  socket.onclose = () => {
    reconnectTimer = setTimeout(connect, 3000)
  }

  socket.onerror = () => {
    socket?.close()
  }

  // Ping every 30s to keep alive
  const ping = setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send('ping')
    else clearInterval(ping)
  }, 30_000)
}

export function useWS(event: string, handler: WSHandler) {
  if (!handlers.has(event)) handlers.set(event, new Set())
  handlers.get(event)!.add(handler)
  connect()

  onUnmounted(() => {
    handlers.get(event)?.delete(handler)
  })
}

// Start connection immediately on import
connect()
