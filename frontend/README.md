# AI模拟面试系统 - 前端项目

## 项目概述

AI模拟面试系统前端基于Vue 3 + TypeScript开发，提供多岗位模拟面试界面，支持语音交互、实时对话和面试报告可视化。

### 核心功能

- **岗位选择**: Java后端、Web前端等岗位选择
- **语音交互**: 语音录制、播放和实时转文字
- **智能对话**: 与AI面试官进行多轮对话
- **实时评估**: 回答后即时获取评分和反馈
- **报告可视化**: 雷达图展示能力评估结果
- **历史记录**: 查看过往面试记录

### 技术栈

- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: axios
- **WebSocket**: socket.io-client
- **图表库**: ECharts

## 项目结构

```
src/
├── api/                  # API接口封装
│   ├── interview.ts     # 面试相关API
│   ├── voice.ts         # 语音服务API
│   ├── websocket.ts     # WebSocket连接
│   └── request.ts       # axios请求拦截器
├── assets/              # 静态资源
│   ├── base.css         # 基础样式
│   ├── main.css         # 主样式
│   └── logo.svg         # Logo
├── components/          # 通用组件
│   ├── AudioRecorder.vue # 音频录制组件
│   ├── MessageBubble.vue # 消息气泡组件
│   ├── ScoreRadar.vue    # 评分雷达图组件
│   └── icons/           # 图标组件
├── router/              # 路由配置
│   └── index.ts         # Vue Router配置
├── stores/              # 状态管理（Pinia）
│   ├── user.ts          # 用户状态
│   ├── interview.ts     # 面试状态
│   └── counter.ts       # 示例状态
├── utils/               # 工具函数
│   ├── audio.ts         # 音频处理工具
│   └── format.ts        # 格式化工具
├── views/               # 页面视图
│   ├── HomeView.vue     # 首页（岗位选择）
│   ├── InterviewView.vue # 面试页面
│   ├── ReportView.vue   # 报告页面
│   └── AboutView.vue    # 关于页面
├── App.vue              # 根组件
└── main.ts              # 应用入口
```

## 快速开始

### 环境要求

- Node.js ^20.19.0 或 >=22.12.0
- npm 或 yarn

### 安装依赖

```sh
npm install
```

### 启动开发服务器

```sh
npm run dev
```

前端将在 http://localhost:5173 启动，并自动代理API请求到后端服务（http://localhost:8083）。

### 生产构建

```sh
npm run build
```

构建产物将生成在 `dist/` 目录中。

### 类型检查

```sh
npm run type-check
```

## 开发指南

### API调用

所有API调用都封装在 `src/api/` 目录下：

- `interview.ts`: 面试相关接口（开始面试、提交回答、获取报告等）
- `voice.ts`: 语音服务接口（ASR、TTS）
- `websocket.ts`: WebSocket连接管理

### 状态管理

使用Pinia进行状态管理，主要store：

- `interview.ts`: 管理面试会话状态、对话历史、当前问题等
- `user.ts`: 管理用户信息（预留）

### 组件说明

1. **AudioRecorder.vue**: 语音录制组件，支持录音、播放和音频处理
2. **MessageBubble.vue**: 对话气泡组件，区分AI和用户消息
3. **ScoreRadar.vue**: 能力评分雷达图组件，使用ECharts绘制

### 页面路由

- `/`: 首页（HomeView.vue） - 岗位选择
- `/interview`: 面试页面（InterviewView.vue） - 主面试界面
- `/report/:id`: 报告页面（ReportView.vue） - 面试报告详情
- `/about`: 关于页面（AboutView.vue）

## 配置说明

### 代理配置

前端Vite配置已设置代理到后端服务：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8083',
      changeOrigin: true
    }
  }
}
```

### 环境变量

开发环境变量配置在 `.env.development` 文件中。

## 开发工具推荐

### IDE设置

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (禁用Vetur)。

### 浏览器扩展

- **Chromium浏览器**:
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - 在Chrome DevTools中开启Custom Object Formatter: http://bit.ly/object-formatters
- **Firefox**:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - 在Firefox DevTools中开启Custom Object Formatter: https://fxdx.dev/firefox-devtools-custom-object-formatters/

## TypeScript支持

TypeScript默认无法处理`.vue`文件的类型信息，因此使用`vue-tsc`代替`tsc`进行类型检查。在编辑器中需要安装[Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar)扩展。

## 相关文档

- **后端API文档**: 参见后端项目README
- **完整项目文档**: 参见 [.md/read_me.md](../.md/read_me.md)
- **前端开发指南**: 参见 [.md/read_me_vue.md](../.md/read_me_vue.md)
