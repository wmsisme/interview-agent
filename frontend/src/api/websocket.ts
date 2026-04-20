// @ts-ignore
import { io, Socket } from 'socket.io-client'

type WebSocketMessage = {
  type: 'start' | 'stop' | 'partial' | 'stopped' | 'started' | 'error'
  [key: string]: any
}

type WebSocketCallbacks = {
  onPartialText?: (text: string) => void
  onFinalText?: (text: string) => void
  onError?: (error: string) => void
  onStarted?: (sessionId: string) => void
}

export class VoiceWebSocket {
  private socket: Socket | null = null
  private callbacks: WebSocketCallbacks = {}
  
  connectAndStart(interviewId: number, questionId: number, callbacks: WebSocketCallbacks) {
    this.callbacks = callbacks
    
    const socketUrl = `http://${import.meta.env.VITE_WS_BASE_URL.replace('ws://', '').replace('wss://', '')}`
    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket'],
      reconnection: false
    })
    
    this.socket.on('connect', () => {
      console.log('Socket.IO connected')
      
      // 加入命名空间
      this.socket!.emit('start', {
        interviewId: interviewId.toString(),
        questionId: questionId.toString()
      }, { namespace: '/ws/stt' })
    })
    
    this.socket.on('started', (data: any) => {
      this.callbacks.onStarted?.(data.sessionId)
    })
    
    this.socket.on('partial', (data: any) => {
      this.callbacks.onPartialText?.(data.text)
    })
    
    this.socket.on('stopped', (data: any) => {
      this.callbacks.onFinalText?.(data.text)
    })
    
    this.socket.on('error', (data: any) => {
      this.callbacks.onError?.(data.message)
    })
    
    this.socket.on('connect_error', (error: Error) => {
      console.error('Socket.IO连接错误:', error)
      this.callbacks.onError?.('WebSocket连接错误')
    })
    
    this.socket.on('disconnect', () => {
      console.log('Socket.IO连接断开')
    })
  }
  
  sendAudioData(audioData: ArrayBuffer) {
    if (this.socket?.connected) {
      // 发送二进制数据
      this.socket.emit('audio', audioData, { namespace: '/ws/stt' })
    }
  }
  
  stop() {
    if (this.socket?.connected) {
      this.socket.emit('stop', {}, { namespace: '/ws/stt' })
    }
    this.close()
  }
  
  close() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
}

export default VoiceWebSocket