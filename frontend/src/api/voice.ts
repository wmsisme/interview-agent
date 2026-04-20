import request from './request'
import axios from 'axios'

/**
 * 文本转语音（使用新的POST API）
 * @param text 要转换的文本
 * @returns 返回音频Blob对象
 */
export const textToSpeech = async (text: string): Promise<Blob> => {
  try {
    // 首先尝试使用新的POST API
    const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/tts`, 
      { text },
      {
        responseType: 'blob',
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    return response.data
  } catch (error) {
    console.warn('TTS POST API失败，尝试使用旧的GET API:', error)
    
    // 如果POST API失败，回退到旧的GET API
    const audioUrl = `${import.meta.env.VITE_API_BASE_URL}/tts?text=${encodeURIComponent(text)}`
    const response = await axios.get(audioUrl, { responseType: 'blob' })
    return response.data
  }
}

/**
 * 语音识别（ASR）
 * @param audioBlob 音频Blob对象（WebM格式）
 * @returns 返回识别出的文本
 */
export const speechToText = async (audioBlob: Blob): Promise<string> => {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  
  const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/asr`, 
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
  
  return response.data.text
}

/**
 * 播放音频Blob
 * @param audioBlob 音频Blob对象
 * @returns Promise
 */
export const playAudioBlob = (audioBlob: Blob): Promise<void> => {
  return new Promise((resolve, reject) => {
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    
    audio.oncanplaythrough = () => {
      audio.play().then(() => {
        // 播放完成后清理URL
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
          resolve()
        }
      }).catch(reject)
    }
    
    audio.onerror = (error) => {
      URL.revokeObjectURL(audioUrl)
      reject(error)
    }
    
    // 设置超时
    setTimeout(() => {
      URL.revokeObjectURL(audioUrl)
      reject(new Error('音频播放超时'))
    }, 30000)
  })
}

/**
 * 播放文本转语音
 * @param text 要转换并播放的文本
 */
export const playTTS = async (text: string): Promise<void> => {
  try {
    const audioBlob = await textToSpeech(text)
    await playAudioBlob(audioBlob)
  } catch (error) {
    console.error('TTS播放失败:', error)
    // 静默失败，不影响主流程
  }
}

/**
 * 将WebM音频转换为PCM格式（用于实时语音识别）
 * @param webmBlob WebM格式的音频Blob
 * @returns PCM格式的ArrayBuffer
 */
export const convertWebmToPcm = async (webmBlob: Blob): Promise<ArrayBuffer> => {
  // 这里简化处理，实际项目中应该使用AudioContext进行转换
  // 或者在后端进行转换
  return await webmBlob.arrayBuffer()
}

/**
 * 旧的播放URL方法（保持向后兼容）
 * @deprecated 请使用playAudioBlob或playTTS
 */
export const playAudioFromUrl = (url: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio(url)
    audio.oncanplaythrough = () => {
      audio.play().then(resolve).catch(reject)
    }
    audio.onerror = reject
  })
}