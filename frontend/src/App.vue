<script setup lang="ts">
import { RouterView } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const locale = zhCn
</script>

<template>
  <ElConfigProvider :locale="locale">
    <div id="app">
      <!-- 应用头部 -->
      <header class="app-header" v-if="false"> <!-- 暂时隐藏头部 -->
        <div class="container">
          <div class="header-content">
            <div class="logo">
              <span class="logo-text">AI面试教练</span>
            </div>
            <nav class="nav-menu">
              <router-link to="/" class="nav-link">首页</router-link>
              <router-link to="/interview" class="nav-link">模拟面试</router-link>
              <router-link to="/about" class="nav-link">关于</router-link>
            </nav>
            <div class="user-menu">
              <el-avatar size="small" />
            </div>
          </div>
        </div>
      </header>

      <!-- 主要内容 -->
      <main class="app-main">
        <RouterView />
      </main>

      <!-- 应用底部 -->
      <footer class="app-footer">
        <div class="container">
          <div class="footer-content">
            <div class="footer-info">
              <p>AI模拟面试教练 &copy; 2024 - 助力计算机专业学生面试准备</p>
              <p class="footer-links">
                <a href="#" class="footer-link">使用条款</a>
                <span class="separator">·</span>
                <a href="#" class="footer-link">隐私政策</a>
                <span class="separator">·</span>
                <a href="#" class="footer-link">联系我们</a>
              </p>
            </div>
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
  background: white;
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  padding: 0.75rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav-link:hover {
  color: var(--primary-color);
}

.nav-link.router-link-exact-active {
  color: var(--primary-color);
  font-weight: 600;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-main {
  flex: 1;
}

.app-footer {
  background: var(--background-color);
  border-top: 1px solid var(--border-color);
  padding: 1.5rem 0;
  margin-top: auto;
}

.footer-content {
  text-align: center;
}

.footer-info {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.footer-info p {
  margin: 0.25rem 0;
}

.footer-links {
  margin-top: 0.5rem;
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: var(--primary-color);
}

.separator {
  margin: 0 0.5rem;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .nav-menu {
    gap: 1rem;
  }
  
  .logo-text {
    font-size: 1rem;
  }
}
</style>