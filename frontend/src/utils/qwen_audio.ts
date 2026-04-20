// Qwen-Omni音频处理工具

export class QwenAudioProcessor {
  private audioContext: AudioContext | null = null
  private sampleRate = 16000 // Qwen-Omni要求16kHz
  
  /**
   * 初始化音频处理器
   */
  async init(): Promise<void> {
    if (!this.audioContext) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      this.audioContext = new AudioContextClass({
        sampleRate: this.sampleRate
      })
      
      // 等待音频上下文恢复（如果被挂起）
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }
    }
  }
  
  /**
   * 将音频Blob转换为PCM 16kHz单声道16-bit格式
   */
  async convertToPCM(audioBlob: Blob): Promise<ArrayBuffer> {
    await this.init()
    
    if (!this.audioContext) {
      throw new Error('音频上下文未初始化')
    }
    
    try {
      // 1. 将Blob转换为AudioBuffer
      const arrayBuffer = await audioBlob.arrayBuffer()
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer)
      
      // 2. 获取原始音频数据
      const sourceChannels = audioBuffer.numberOfChannels
      const sourceSampleRate = audioBuffer.sampleRate
      const sourceLength = audioBuffer.length
      
      console.log(`音频信息: ${sourceChannels}声道, ${sourceSampleRate}Hz, ${sourceLength}个采样点`)
      
      // 3. 重采样到16kHz
      const targetLength = Math.floor(sourceLength * this.sampleRate / sourceSampleRate)
      const pcmData = new Int16Array(targetLength)
      
      // 4. 混合多声道为单声道并重采样
      for (let i = 0; i < targetLength; i++) {
        const sourceIndex = Math.floor(i * sourceSampleRate / this.sampleRate)
        let sample = 0
        
        // 混合所有声道
        for (let channel = 0; channel < sourceChannels; channel++) {
          const channelData = audioBuffer.getChannelData(channel)
          if (sourceIndex < channelData.length) {
            sample += channelData[sourceIndex]!
          }
        }
        
        // 平均声道并转换为16-bit PCM
        sample /= sourceChannels
        pcmData[i] = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)))
      }
      
      return pcmData.buffer
      
    } catch (error) {
      console.error('音频转换失败:', error)
      throw error
    }
  }
  
  /**
   * 验证PCM数据格式
   * @param pcmBuffer PCM音频数据
   * @param expectedSampleRate 期望的采样率，默认16000
   * @param expectedChannels 期望的声道数，默认1
   * @param expectedBits 期望的位深度，默认16
   */
  validatePCM(pcmBuffer: ArrayBuffer, expectedSampleRate: number = 16000, expectedChannels: number = 1, expectedBits: number = 16): boolean {
    try {
      // 检查数据大小
      const byteLength = pcmBuffer.byteLength
      const sampleSize = expectedBits / 8 // 每个采样的字节数
      const expectedLength = byteLength / (expectedChannels * sampleSize)
      
      console.log(`PCM验证: ${byteLength}字节, 期望${expectedChannels}声道, ${expectedBits}位, 约${expectedLength}个采样点`)
      
      // 简单的完整性检查
      if (byteLength % (expectedChannels * sampleSize) !== 0) {
        console.error(`PCM数据大小不匹配: ${byteLength}字节不是${expectedChannels}声道${expectedBits}位的整数倍`)
        return false
      }
      
      // 检查数据范围（对于16-bit PCM，值应在-32768到32767之间）
      if (expectedBits === 16) {
        const pcmData = new Int16Array(pcmBuffer)
        let min = 32767
        let max = -32768
        for (let i = 0; i < Math.min(pcmData.length, 1000); i++) { // 只检查前1000个样本
          const value = pcmData[i]!
          if (value < min) min = value
          if (value > max) max = value
        }
        console.log(`PCM数据范围: ${min} 到 ${max} (16-bit期望范围: -32768到32767)`)
        
        if (min < -32768 || max > 32767) {
          console.error(`PCM数据超出16-bit范围: ${min} 到 ${max}`)
          return false
        }
      }
      
      return true
    } catch (error) {
      console.error('PCM验证失败:', error)
      return false
    }
  }
  
  /**
   * 将PCM ArrayBuffer转换为Base64字符串
   */
  pcmToBase64(pcmBuffer: ArrayBuffer): string {
    try {
      // 创建Uint8Array视图
      const uint8Array = new Uint8Array(pcmBuffer)
      
      // 转换为Base64
      let binary = ''
      const bytes = new Uint8Array(pcmBuffer)
      const len = bytes.byteLength
      for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]!)
      }
      
      return window.btoa(binary)
    } catch (error) {
      console.error('Base64转换失败:', error)
      throw error
    }
  }
  
  /**
   * 播放Base64编码的PCM音频
   */
  async playPCMBase64(base64Data: string): Promise<void> {
    await this.init()
    
    if (!this.audioContext) {
      throw new Error('音频上下文未初始化')
    }
    
    try {
      // 1. 解码Base64
      const binary = window.atob(base64Data)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
      }
      
      // 2. 将16-bit PCM转换为Float32
      const pcmData = new Int16Array(bytes.buffer)
      const floatData = new Float32Array(pcmData.length)
      
      for (let i = 0; i < pcmData.length; i++) {
        floatData[i] = pcmData[i]! / 32768.0 // 16-bit PCM归一化到[-1, 1]
      }
      
      // 3. 创建AudioBuffer
      const audioBuffer = this.audioContext.createBuffer(1, floatData.length, this.sampleRate)
      audioBuffer.copyToChannel(floatData, 0)
      
      // 4. 播放音频
      const source = this.audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(this.audioContext.destination)
      
      return new Promise((resolve) => {
        source.onended = () => resolve()
        source.start()
      })
      
    } catch (error) {
      console.error('播放PCM音频失败:', error)
      throw error
    }
  }
  
  /**
   * 获取麦克风流并转换为16kHz PCM
   */
  async getMicrophoneStream(
    onAudioData: (pcmBuffer: ArrayBuffer) => void,
    onError?: (error: Error) => void
  ): Promise<() => void> {
    await this.init()
    
    if (!this.audioContext) {
      throw new Error('音频上下文未初始化')
    }
    
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.sampleRate,
          channelCount: 1, // 单声道
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      // 创建音频源
      const source = this.audioContext.createMediaStreamSource(stream)
      
      // 创建ScriptProcessor（处理音频数据）
      // 使用512缓冲区大小（32ms @ 16kHz = 1024字节），可以分割为800字节（25ms）的帧
      const processor = this.audioContext.createScriptProcessor(512, 1, 1)
      
      processor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0)
        
        // 转换为16-bit PCM
        const pcmData = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, Math.round(inputData[i]! * 32767)))
        }
        
        onAudioData(pcmData.buffer)
      }
      
      // 连接节点
      source.connect(processor)
      processor.connect(this.audioContext.destination)
      
      // 返回清理函数
      return () => {
        processor.disconnect()
        source.disconnect()
        stream.getTracks().forEach(track => track.stop())
      }
      
    } catch (error) {
      console.error('获取麦克风流失败:', error)
      if (onError) {
        onError(error as Error)
      }
      throw error
    }
  }
  
  /**
   * 销毁音频处理器
   */
  destroy(): void {
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
  }
}

// 单例实例
let audioProcessorInstance: QwenAudioProcessor | null = null

export function getQwenAudioProcessor(): QwenAudioProcessor {
  if (!audioProcessorInstance) {
    audioProcessorInstance = new QwenAudioProcessor()
  }
  return audioProcessorInstance
}