import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface UserProfile {
  id?: number
  nickname: string
  avatar?: string
  email?: string
  experience?: string // 工作经验：'student', 'junior', 'senior', 'expert'
  targetPositions?: string[] // 目标岗位
  createdAt?: Date
}

export const useUserStore = defineStore('user', () => {
  // 用户状态
  const isLoggedIn = ref(false)
  const profile = ref<UserProfile>({
    nickname: '访客用户',
    experience: 'student',
    targetPositions: ['java_backend', 'web_frontend']
  })
  const token = ref<string | null>(null)
  const permissions = ref<string[]>([])

  // 登录
  const login = async (credentials: { username: string; password: string }) => {
    // 模拟登录逻辑
    isLoggedIn.value = true
    profile.value = {
      id: 1,
      nickname: credentials.username,
      email: `${credentials.username}@example.com`,
      experience: 'student',
      targetPositions: ['java_backend', 'web_frontend']
    }
    token.value = 'mock-jwt-token'
    permissions.value = ['interview', 'report_view']
    
    return { success: true, token: token.value }
  }

  // 注销
  const logout = () => {
    isLoggedIn.value = false
    profile.value = {
      nickname: '访客用户',
      experience: 'student',
      targetPositions: ['java_backend', 'web_frontend']
    }
    token.value = null
    permissions.value = []
  }

  // 更新个人资料
  const updateProfile = async (updates: Partial<UserProfile>) => {
    profile.value = { ...profile.value, ...updates }
    return { success: true }
  }

  // 检查权限
  const hasPermission = (permission: string) => {
    return permissions.value.includes(permission)
  }

  // 获取用户头像URL
  const getAvatarUrl = () => {
    return profile.value.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.value.nickname)}&background=random`
  }

  return {
    // 状态
    isLoggedIn,
    profile,
    token,
    permissions,
    
    // 动作
    login,
    logout,
    updateProfile,
    hasPermission,
    getAvatarUrl
  }
})