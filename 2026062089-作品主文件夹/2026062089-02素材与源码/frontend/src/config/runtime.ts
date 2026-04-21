const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')

const defaultApiBaseUrl = '/api'

const getDefaultWsBaseUrl = () => {
  if (typeof window === 'undefined') {
    return 'ws://localhost:5173'
  }

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${wsProtocol}//${window.location.host}`
}

export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl
)

export const WS_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_WS_BASE_URL || getDefaultWsBaseUrl()
)

export const SOCKET_HTTP_BASE_URL = `${WS_BASE_URL.startsWith('wss://') ? 'https://' : 'http://'}${WS_BASE_URL
  .replace(/^ws:\/\//, '')
  .replace(/^wss:\/\//, '')}`
