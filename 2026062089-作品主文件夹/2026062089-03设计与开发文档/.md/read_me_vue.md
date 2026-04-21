1. 项目概述
本项目为“AI模拟面试与能力提升软件”的前端部分，基于 Vue 3 开发，旨在为计算机专业学生提供一个简洁、易用、专注的模拟面试环境。核心功能包括：

选择目标岗位（Java后端 / Web前端）

与AI面试官进行多轮语音/文字对话

实时获取多维度能力评估与反馈

查看历史面试报告与能力成长趋势

设计原则：操作简单、界面清晰、无多余功能，让面试者能快速开始练习，专注于面试本身。

2. 技术栈
类别	技术选型	说明
核心框架	Vue 3	组合式API + <script setup> 语法
构建工具	Vite	快速启动与热更新
UI 组件库	Element Plus	整洁、专业的组件，符合企业级风格
状态管理	Pinia	轻量级状态管理，适合面试会话
路由	Vue Router 4	页面导航
HTTP 请求	Axios	与后端REST API通信
录音处理	Web Audio API	实现麦克风录音与音频数据获取
音频播放	HTML5 Audio	播放AI合成的语音
图表展示	ECharts	显示能力雷达图、成长曲线（可选）
TypeScript	是	提高代码可维护性与类型安全
3. 项目结构
text
src/
├── assets/               # 静态资源（图片、字体等）
├── components/           # 可复用组件
│   ├── AudioRecorder.vue # 录音按钮与波形显示（可选）
│   ├── MessageBubble.vue # 对话气泡（区分AI/用户）
│   ├── ScoreRadar.vue    # 能力雷达图组件
│   └── ReportCard.vue    # 报告摘要卡片
├── views/                # 页面级组件
│   ├── HomeView.vue      # 岗位选择页
│   ├── InterviewView.vue # 模拟面试主界面
│   └── ReportView.vue    # 面试报告详情页
├── stores/               # Pinia 状态存储
│   ├── interview.js      # 当前面试会话状态
│   └── user.js           # 用户信息
├── router/               # 路由配置
│   └── index.js
├── api/                  # 后端接口封装
│   ├── interview.js      # 面试相关API
│   ├── voice.js          # 语音服务API
│   └── user.js           # 用户相关API
├── utils/                # 工具函数
│   ├── audio.js          # 录音、音频格式转换
│   └── format.js         # 数据格式化
├── App.vue
└── main.js
4. 页面设计详述
4.1 岗位选择页 (HomeView.vue)
目标：让面试者一眼选择目标岗位，快速开始。

界面元素：

页面标题：AI模拟面试教练

两个大卡片，分别展示“Java后端开发工程师”和“Web前端开发工程师”

卡片内包含岗位简介（如核心技术栈）

点击卡片即进入对应岗位的面试

底部可放置用户信息（如昵称、历史记录入口）

交互流程：

用户进入首页，看到两个岗位卡片。

点击任一卡片，系统自动创建面试会话，跳转到面试主界面。

代码要点：

使用 Element Plus el-card 组件，配合 hover 效果。

点击后调用 interviewStore.startInterview(positionId) 并跳转。

4.2 模拟面试主界面 (InterviewView.vue)
目标：模拟真实面试对话，支持语音和文字输入，操作简单。

界面布局（从上到下）：

顶部状态栏：显示当前岗位、面试轮次（第几题）、结束按钮。

对话区域：展示历史对话消息，AI消息与用户消息左右分明，最新消息自动滚动到底部。

AI消息：左侧显示头像（机器人图标），文字内容 + 播放语音按钮（可重听）

用户消息：右侧显示头像（用户图标），文字内容（语音回答转写后显示）

底部输入区：

左侧：切换输入方式图标（文本输入框 / 录音按钮）

右侧：发送按钮（文本模式）或录音按钮（长按说话）

实时反馈卡片（可选，但建议简洁）：可放在对话区域上方或侧边，显示当前回答的初步评分（如技术分、表达分），避免干扰。

关键交互细节：

文本输入模式：显示输入框，用户打字后点击发送，消息立即显示，并进入等待AI回复状态。

语音输入模式：

长按录音按钮（麦克风图标），开始录音；松开后自动发送音频。

录音时按钮有动画反馈（如波纹扩散、颜色变化）。

发送后，用户语音转写的文本显示在对话气泡中。

AI回复：后端返回文本后，前端自动调用TTS接口合成语音并播放（可静音/重播）。

等待状态：AI回复期间显示“AI正在思考...”的加载提示。

状态管理（Pinia）：

javascript
// stores/interview.js
export const useInterviewStore = defineStore('interview', {
  state: () => ({
    interviewId: null,
    position: null,
    messages: [], // { role: 'ai'|'user', content: string, audioUrl?: string, scores?: object }
    currentQuestion: null,
    isLoading: false,
    finished: false
  }),
  actions: {
    async startInterview(positionId) { ... },
    async sendAnswer(answerText, audioBlob) { ... },
    async fetchNextQuestion() { ... },
    async endInterview() { ... }
  }
})
核心组件实现：

4.2.1 录音组件 (AudioRecorder.vue)
使用 navigator.mediaDevices.getUserMedia 获取麦克风权限。

利用 MediaRecorder API 录制音频，输出格式为 audio/webm。

提供 startRecording、stopRecording 方法，通过自定义事件向上传递音频Blob。

录音时长限制（如60秒），过长自动停止。

vue
<script setup>
import { ref } from 'vue'
const emit = defineEmits(['record-start', 'record-stop', 'audio-ready'])
let mediaRecorder = null
let audioChunks = []

const startRecording = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  mediaRecorder = new MediaRecorder(stream)
  audioChunks = []
  mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data)
  mediaRecorder.onstop = () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
    emit('audio-ready', audioBlob)
    stream.getTracks().forEach(track => track.stop())
  }
  mediaRecorder.start()
  emit('record-start')
}
const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
    emit('record-stop')
  }
}
</script>
4.2.2 对话气泡组件 (MessageBubble.vue)
根据 role 决定样式（左/右对齐、背景色）。

显示文本内容，若为AI消息且有音频URL，显示小喇叭图标，点击播放。

使用 props 接收消息对象。

4.3 面试报告页 (ReportView.vue)
目标：清晰展示面试结果，包括多维度评分和改进建议，引导后续练习。

界面内容：

头部：面试岗位、日期、总评分（如82分）。

能力雷达图：展示技术、深度、逻辑、表达、匹配度五个维度的得分（0-10分）。

亮点与不足：列表形式展示本次面试的优点和待改进项。

提升建议：根据评估结果推荐的学习资源或练习方向（如“推荐复习Java并发编程”）。

底部按钮：返回首页 / 重新面试 / 查看历史。

图表实现：

使用 ECharts 雷达图，配置五个维度，数据从接口返回。

简单易读，不添加多余交互。

4.4 历史记录页（可选，简单列表）
如果希望展示历史面试，可用简洁的表格或卡片列表，显示时间、岗位、总分，点击进入报告。

5. 与后端接口对接
5.1 API 封装 (使用 Axios)
创建 api/request.js 配置基础URL、拦截器。

javascript
import axios from 'axios'
const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})
// 请求/响应拦截器...
export default instance
各模块API示例：

api/interview.js

javascript
import request from './request'

export const startInterview = (positionId) => {
  return request.post('/interview/start', { positionId })
}

export const submitAnswer = (interviewId, questionId, answerText) => {
  return request.post('/interview/answer', { interviewId, questionId, answerText })
}

export const submitAudioAnswer = (interviewId, questionId, audioBlob) => {
  const formData = new FormData()
  formData.append('interviewId', interviewId)
  formData.append('questionId', questionId)
  formData.append('audio', audioBlob)
  return request.post('/interview/answer/audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getReport = (interviewId) => {
  return request.get(`/interview/report/${interviewId}`)
}
api/voice.js

javascript
import request from './request'

export const textToSpeech = (text) => {
  // 返回音频文件blob
  return request.post('/tts', { text }, { responseType: 'blob' })
}
WebSocket 连接（用于实时语音识别）：

使用原生 WebSocket 建立连接，路径为 /stt?userId=xxx&interviewId=xxx&questionId=xxx。

当用户录音时，通过 WebSocket 发送音频数据（二进制），后端返回识别文本。

识别文本可实时显示或作为最终答案提交。

5.2 状态管理中的异步操作
在 Pinia store 中调用 API，并更新状态。

javascript
actions: {
  async startInterview(positionId) {
    const res = await startInterview(positionId)
    this.interviewId = res.data.interviewId
    this.position = res.data.position
    this.messages = [{ role: 'ai', content: res.data.firstQuestion, audioUrl: res.data.audioUrl }]
    this.currentQuestion = res.data.firstQuestion
  },
  async sendAnswer(answerText, audioBlob) {
    // 先显示用户消息
    this.messages.push({ role: 'user', content: answerText })
    this.isLoading = true
    try {
      let res
      if (audioBlob) {
        res = await submitAudioAnswer(this.interviewId, this.currentQuestionId, audioBlob)
      } else {
        res = await submitAnswer(this.interviewId, this.currentQuestionId, answerText)
      }
      // 处理返回的评估和下一题
      const { scores, feedback, nextQuestion, nextAudioUrl } = res.data
      // 可显示当前回答的反馈（可选）
      this.messages.push({ role: 'ai', content: feedback, audioUrl: nextAudioUrl }) // 或单独显示反馈
      if (nextQuestion) {
        this.messages.push({ role: 'ai', content: nextQuestion, audioUrl: nextAudioUrl })
        this.currentQuestion = nextQuestion
      } else {
        this.finished = true
        // 跳转到报告页
      }
    } finally {
      this.isLoading = false
    }
  }
}
6. 环境配置与运行
6.1 环境变量
创建 .env.development 和 .env.production 文件：

text
VITE_API_BASE_URL=http://localhost:8080/api
VITE_WS_BASE_URL=ws://localhost:8080
6.2 安装与启动
bash
# 安装依赖
npm install

# 开发环境运行
npm run dev

# 构建生产版本
npm run build
6.3 代码规范
使用 ESLint + Prettier 统一代码风格。

组件命名采用 PascalCase，文件命名采用 kebab-case。

7. 开发步骤建议（前端）
阶段	任务	产出
第1周	搭建Vue项目，配置路由、Pinia、Element Plus；实现岗位选择页	可切换岗位，点击跳转面试页（空）
第2周	实现面试主界面UI：对话区域、文本输入框、录音按钮（仅UI逻辑）；集成Axios，对接后端纯文本接口	能进行纯文本对话，显示消息
第3周	实现录音功能（Web Audio API），对接WebSocket语音识别；实现语音合成播放	支持语音输入，AI语音回复
第4周	实现报告页（雷达图、建议），对接报告接口；完善历史记录、用户体验细节；项目优化与文档整理	完整可演示的前端应用
8. 注意事项
简洁至上：每个页面只保留核心功能，避免无关的动画或装饰。

错误处理：网络异常、麦克风权限拒绝等情况给出友好提示。

响应式：适配主流PC屏幕尺寸（至少1366x768）。

浏览器兼容：使用现代浏览器（Chrome、Edge最新版）。

录音格式：确保与后端约定的音频格式一致（如PCM 16000Hz单声道），可能需在前端转换格式（可使用 audioContext 重采样）。

9. 与后端联调要点
提前约定接口数据结构（JSON Schema）。

语音相关：明确音频格式、采样率、编码方式。

WebSocket连接：携带认证参数（如token），处理重连机制。

