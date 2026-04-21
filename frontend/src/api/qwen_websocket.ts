// Qwen-Omni WebSocket客户端（使用Socket.IO）
// @ts-ignore
import { io, Socket } from 'socket.io-client'
import { SOCKET_HTTP_BASE_URL } from '@/config/runtime'

export type QwenWebSocketMessage = {
  type: 'audio' | 'text' | 'started' | 'stopped' | 'error' | 'rag_results'
  data?: any
  sessionId?: string
  message?: string
}

export type QwenWebSocketCallbacks = {
  onAudio?: (audioBase64: string) => void
  onText?: (textChunk: string) => void
  onStarted?: (sessionId: string) => void
  onStopped?: (sessionId: string) => void
  onError?: (error: string) => void
  onRagResults?: (query: string, results: any[]) => void
}

export class QwenWebSocket {
  private socket: Socket | null = null
  private callbacks: QwenWebSocketCallbacks = {}
  private sessionId: string | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private isConnecting = false
  
  constructor() {
    this.connect = this.connect.bind(this)
    this.disconnect = this.disconnect.bind(this)
    this.sendAudio = this.sendAudio.bind(this)
    this.sendImage = this.sendImage.bind(this)
  }
  
  connect(sessionId: string, interviewId: string, position: string, callbacks: QwenWebSocketCallbacks) {
    if (this.isConnecting) {
      console.warn('WebSocket连接正在进行中')
      return
    }
    
    this.isConnecting = true
    this.sessionId = sessionId
    this.callbacks = callbacks
    this.reconnectAttempts = 0
    
    const namespace = '/ws/qwen'
    
    console.log(`连接Qwen-Omni Socket.IO: ${SOCKET_HTTP_BASE_URL}, 命名空间: ${namespace}`)
    
    try {
      this.socket = io(`${SOCKET_HTTP_BASE_URL}${namespace}`, {
        path: '/socket.io',
        transports: ['websocket'],
        reconnection: false,
        query: {
          sessionId,
          interviewId,
          position
        }
      })
      
      this.socket.on('connect', () => {
        console.log('Socket.IO连接已建立')
        this.isConnecting = false
        this.reconnectAttempts = 0
        
        // 发送开始面试消息
        this.sendStartInterview(interviewId, position)
      })
      
      this.socket.on('audio', (data: any) => {
        this.callbacks.onAudio?.(data.data)
      })
      
      this.socket.on('text', (data: any) => {
        this.callbacks.onText?.(data.data)
      })
      
      this.socket.on('started', (data: any) => {
        this.callbacks.onStarted?.(data.sessionId)
      })
      
      this.socket.on('stopped', (data: any) => {
        this.callbacks.onStopped?.(data.sessionId)
      })
      
      this.socket.on('error', (data: any) => {
        this.callbacks.onError?.(data.message || '未知错误')
      })
      
      this.socket.on('rag_results', (data: any) => {
        this.callbacks.onRagResults?.(data.query, data.results || [])
      })
      
      this.socket.on('connect_error', (error: Error) => {
        console.error('Socket.IO连接错误:', error)
        this.isConnecting = false
        this.callbacks.onError?.('WebSocket连接错误')
      })
      
      this.socket.on('disconnect', (reason: string) => {
        console.log(`Socket.IO连接断开: ${reason}`)
        this.isConnecting = false
        
        // 如果不是正常断开，尝试重连
        if (reason !== 'io server disconnect') {
          this.reconnect(interviewId, position)
        }
      })
      
    } catch (error) {
      console.error('创建Socket.IO连接失败:', error)
      this.isConnecting = false
      this.callbacks.onError?.('创建WebSocket连接失败')
    }
  }
  
  private sendStartInterview(interviewId: string, position: string) {
    if (this.socket?.connected) {
      this.socket.emit('start_interview', {
        interviewId,
        position
      })
    }
  }
  

  
  sendAudio(audioBase64: string) {
    if (this.socket?.connected) {
      this.socket.emit('audio', {
        data: audioBase64
      })
    }
  }
  
  sendAudioBlob(audioBlob: Blob) {
    if (this.socket?.connected) {
      const reader = new FileReader()
      reader.onload = () => {
        const base64Data = reader.result as string
        // 移除数据URL前缀
        const base64 = base64Data.replace(/^data:[^;]+;base64,/, '')
        this.socket!.emit('audio', {
          data: base64
        })
      }
      reader.readAsDataURL(audioBlob)
    }
  }
  
  sendImage(imageBase64: string) {
    if (this.socket?.connected) {
      this.socket.emit('image', {
        data: imageBase64
      })
    }
  }
  
  sendStopInterview() {
    if (this.socket?.connected) {
      this.socket.emit('stop_interview', {})
    }
  }
  
  sendRagQuery(query: string, position: string) {
    if (this.socket?.connected) {
      this.socket.emit('rag_query', {
        query,
        position
      })
    }
  }
  
  private reconnect(interviewId: string, position: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1)
      
      console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连...`)
      
      setTimeout(() => {
        if (this.sessionId && interviewId && position) {
          this.connect(this.sessionId, interviewId, position, this.callbacks)
        }
      }, Math.min(delay, 30000)) // 最大延迟30秒
    } else {
      console.error('达到最大重连次数，连接失败')
      this.callbacks.onError?.('WebSocket连接失败，请刷新页面重试')
    }
  }
  
  disconnect() {
    if (this.socket) {
      this.sendStopInterview()
      this.socket.disconnect()
      this.socket = null
    }
    this.isConnecting = false
    this.sessionId = null
  }
  
  isConnected(): boolean {
    return this.socket !== null && this.socket.connected
  }
}

export default QwenWebSocket
