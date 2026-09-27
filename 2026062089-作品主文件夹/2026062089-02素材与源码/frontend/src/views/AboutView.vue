<template>
  <div class="about-view">
    <div class="hero-section">
      <div class="container">
        <div class="section-badge">关于我们</div>
        <h1 class="hero-title">AI模拟面试教练</h1>
        <p class="hero-subtitle">
          专为计算机专业学生打造的智能面试练习平台
        </p>
      </div>
    </div>

    <div class="content-section">
      <div class="container">
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <h3>AI视频面试</h3>
            <p>基于大语言模型的实时视频面试模拟，支持语音识别与合成，提供身临其境的面试体验。</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            </div>
            <h3>智能评估报告</h3>
            <p>从多维度分析面试表现，生成详细的能力评估报告和改进建议，助你针对性提升。</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <h3>多岗位覆盖</h3>
            <p>涵盖Java后端、Web前端、全栈、大数据等多个技术岗位，满足不同方向面试需求。</p>
          </div>
        </div>

        <div class="tech-section">
          <h2>技术栈</h2>
          <div class="tech-grid">
            <div class="tech-group">
              <h4>前端</h4>
              <div class="tech-tags">
                <el-tag size="small" round>Vue 3</el-tag>
                <el-tag size="small" round>TypeScript</el-tag>
                <el-tag size="small" round>Element Plus</el-tag>
                <el-tag size="small" round>ECharts</el-tag>
                <el-tag size="small" round>Pinia</el-tag>
              </div>
            </div>
            <div class="tech-group">
              <h4>后端</h4>
              <div class="tech-tags">
                <el-tag size="small" round type="success">Python Flask</el-tag>
                <el-tag size="small" round type="success">Socket.IO</el-tag>
                <el-tag size="small" round type="success">MySQL</el-tag>
                <el-tag size="small" round type="success">RAG</el-tag>
              </div>
            </div>
            <div class="tech-group">
              <h4>AI能力</h4>
              <div class="tech-tags">
                <el-tag size="small" round type="warning">LLM对话</el-tag>
                <el-tag size="small" round type="warning">语音识别</el-tag>
                <el-tag size="small" round type="warning">语音合成</el-tag>
                <el-tag size="small" round type="warning">视频分析</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-view {
  min-height: 100vh;
  background: var(--background-color);
}

.hero-section {
  padding: 4rem 0;
  background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 30%, #2563eb 100%);
  text-align: center;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.section-badge {
  display: inline-block;
  padding: 0.25rem 0.875rem;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hero-title {
  font-size: 2.75rem;
  font-weight: 800;
  color: white;
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 1.15rem;
  color: rgba(255, 255, 255, 0.65);
  max-width: 500px;
  margin: 0 auto;
}

.content-section {
  padding: 4rem 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 4rem;
}

.feature-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 2rem;
  text-align: center;
  transition: all var(--transition-base);
}

.feature-card:hover {
  border-color: transparent;
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: var(--primary-lighter);
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.25rem;
}

.feature-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.feature-card p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.tech-section h2 {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 2rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.tech-group {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
}

.tech-group h4 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.875rem;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }

  .features-grid,
  .tech-grid {
    grid-template-columns: 1fr;
  }

  .content-section {
    padding: 2.5rem 0;
  }
}
</style>
