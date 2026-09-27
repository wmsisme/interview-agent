<script setup lang="ts">
import { RouterView, useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const locale = zhCn
const router = useRouter()
const route = useRoute()

const isHomePage = computed(() => route.path === '/')
</script>

<template>
  <ElConfigProvider :locale="locale">
    <div id="app">
      <header class="app-header" :class="{ 'header-transparent': isHomePage }">
        <div class="container">
          <div class="header-content">
            <div class="logo" @click="router.push('/')">
              <div class="logo-icon">
                <svg viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
                  <path d="M10 22V12l6 6-6 4z" fill="white"/>
                  <path d="M22 10v10l-6-6 6-4z" fill="rgba(255,255,255,0.7)"/>
                  <defs>
                    <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
                      <stop stop-color="#3b82f6"/>
                      <stop offset="1" stop-color="#8b5cf6"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span class="logo-text">AI面试教练</span>
            </div>
            <nav class="nav-menu">
              <router-link to="/" class="nav-link" active-class="nav-link-active">
                <span class="nav-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                </span>
                首页
              </router-link>
              <router-link to="/interview/video" class="nav-link" active-class="nav-link-active">
                <span class="nav-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                </span>
                模拟面试
              </router-link>
              <router-link to="/about" class="nav-link" active-class="nav-link-active">
                <span class="nav-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                </span>
                关于
              </router-link>
            </nav>
            <div class="header-actions">
              <el-button
                type="primary"
                size="small"
                round
                @click="router.push('/interview/video')"
                class="cta-button"
              >
                开始面试
                <span class="cta-arrow">→</span>
              </el-button>
            </div>
          </div>
        </div>
      </header>

      <main class="app-main">
        <RouterView v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>

      <footer class="app-footer">
        <div class="container">
          <div class="footer-grid">
            <div class="footer-brand">
              <div class="footer-logo">
                <div class="logo-icon small">
                  <svg viewBox="0 0 32 32" fill="none">
                    <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
                    <path d="M10 22V12l6 6-6 4z" fill="white"/>
                    <path d="M22 10v10l-6-6 6-4z" fill="rgba(255,255,255,0.7)"/>
                    <defs>
                      <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
                        <stop stop-color="#3b82f6"/>
                        <stop offset="1" stop-color="#8b5cf6"/>
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
                <span class="footer-brand-name">AI面试教练</span>
              </div>
              <p class="footer-description">
                专为计算机专业学生打造的智能面试练习平台，助力轻松应对技术面试。
              </p>
            </div>
            <div class="footer-links-group">
              <h4 class="footer-heading">快速导航</h4>
              <router-link to="/" class="footer-link">首页</router-link>
              <router-link to="/interview/video" class="footer-link">模拟面试</router-link>
              <router-link to="/about" class="footer-link">关于我们</router-link>
            </div>
            <div class="footer-links-group">
              <h4 class="footer-heading">面试岗位</h4>
              <span class="footer-link">Java后端开发</span>
              <span class="footer-link">Web前端开发</span>
              <span class="footer-link">全栈工程师</span>
              <span class="footer-link">大数据工程师</span>
            </div>
            <div class="footer-links-group">
              <h4 class="footer-heading">关于项目</h4>
              <p class="footer-copyright">
                AI模拟面试教练 &copy; 2024<br>
                助力计算机专业学生面试准备
              </p>
            </div>
          </div>
          <div class="footer-bottom">
            <span>使用条款</span>
            <span class="separator">·</span>
            <span>隐私政策</span>
            <span class="separator">·</span>
            <span>联系我们</span>
          </div>
        </div>
      </footer>
    </div>
  </ElConfigProvider>
</template>

<style scoped>
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  transition: all var(--transition-base);
  padding: 0;
}

.app-header.header-transparent {
  background: rgba(255, 255, 255, 0);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  border-bottom-color: transparent;
}

.app-header.header-transparent .nav-link {
  color: rgba(255, 255, 255, 0.85);
}

.app-header.header-transparent .nav-link:hover {
  color: white;
}

.app-header.header-transparent .nav-link-active {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

.app-header.header-transparent .logo-text {
  color: white;
}

.app-header.header-transparent .footer-logo,
.app-header.header-transparent .footer-brand-name {
  color: white;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.logo-icon.small {
  width: 28px;
  height: 28px;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
  display: block;
}

.logo-text {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  transition: color var(--transition-base);
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  background: rgba(241, 245, 249, 0.5);
  border-radius: var(--radius-xl);
  padding: 0.25rem;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.7);
}

.nav-link-active {
  color: var(--primary-color) !important;
  background: white !important;
  box-shadow: var(--shadow-sm);
}

.nav-icon {
  display: flex;
  align-items: center;
  opacity: 0.7;
}

.nav-link-active .nav-icon {
  opacity: 1;
}

.header-actions {
  display: flex;
  align-items: center;
}

.cta-button {
  font-weight: 600;
  letter-spacing: 0.01em;
  transition: all var(--transition-base);
}

.cta-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--primary-glow);
}

.cta-arrow {
  margin-left: 2px;
  transition: transform var(--transition-fast);
  display: inline-block;
}

.cta-button:hover .cta-arrow {
  transform: translateX(3px);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.app-footer {
  background: var(--text-primary);
  color: rgba(255, 255, 255, 0.7);
  padding: 3rem 0 1.5rem;
  margin-top: auto;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.footer-brand-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
}

.footer-description {
  font-size: 0.875rem;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.55);
  max-width: 280px;
}

.footer-links-group {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.footer-heading {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 0.25rem;
}

.footer-link {
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color var(--transition-fast);
  cursor: pointer;
}

.footer-link:hover {
  color: white;
}

.footer-copyright {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.6;
}

.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

.separator {
  margin: 0 0.25rem;
  color: rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .header-content {
    height: 56px;
  }

  .nav-menu {
    display: none;
  }

  .logo-text {
    font-size: 1rem;
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .footer-brand {
    grid-column: 1 / -1;
  }
}
</style>
