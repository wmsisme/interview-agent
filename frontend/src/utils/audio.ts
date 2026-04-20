export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null
  private audioChunks: Blob[] = []
  private onDataAvailableCallback: ((data: Blob) => void) | null = null
  private stream: MediaStream | null = null
  
  setOnDataAvailable(callback: (data: Blob) => void) {
    this.onDataAvailableCallback = callback
  }

  async startRecording(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      })
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      this.audioChunks = []
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
          if (this.onDataAvailableCallback) {
            this.onDataAvailableCallback(event.data)
          }
        }
      }
      
      this.mediaRecorder.start(100) // 每100ms收集一次数据
    } catch (error) {
      throw new Error('无法访问麦克风: ' + (error as Error).message)
    }
  }
  
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
        reject(new Error('录音未开始'))
        return
      }
      
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
        this.cleanup()
        resolve(audioBlob)
      }
      
      this.mediaRecorder.stop()
    })
  }
  
  cancelRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop()
    }
    this.cleanup()
  }
  
  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }
    this.mediaRecorder = null
    this.audioChunks = []
  }
  
  getRecordingTime(): number {
    // 简单实现：返回估计的录音时间
    // 实际项目中可以根据audioChunks大小估算
    return this.audioChunks.length * 100 // 近似值
  }
}

export async function convertToPCM(webmBlob: Blob): Promise<ArrayBuffer> {
  // 使用AudioContext进行音频格式转换
  // 这里简化处理，实际项目中需要实现完整的转换逻辑
  return await webmBlob.arrayBuffer()
}

export function createAudioWaveformCanvas(
  canvas: HTMLCanvasElement,
  audioData: ArrayBuffer
): void {
  // 创建音频波形可视化
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#3b82f6'
  
  // 简化波形绘制
  const data = new Uint8Array(audioData.slice(0, 1000))
  if (data.length === 0) return
  
  const barWidth = canvas.width / data.length
  
  for (let i = 0; i < data.length; i++) {
    const barHeight = (data[i]! / 255) * canvas.height
    ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth - 1, barHeight)
  }
}