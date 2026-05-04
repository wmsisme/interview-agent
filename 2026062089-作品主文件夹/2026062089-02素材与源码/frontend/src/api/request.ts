import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { API_BASE_URL } from '@/config/runtime'

const request: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config.responseType === 'blob') {
      return response.data
    }
    
    const res = response.data
    if (res.code !== 200 && res.code !== undefined) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data !== undefined ? res.data : res
  },
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      ElMessage.error('网络连接失败，请检查网络')
    } else if (error.response?.status === 401) {
      ElMessage.error('未授权，请重新登录')
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
