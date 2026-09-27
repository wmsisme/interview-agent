import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/interview/video',
      name: 'video-interview',
      component: () => import('../views/VideoInterviewView.vue'),
      meta: {
        requiresInterview: true
      }
    },
    {
      path: '/report/:id',
      name: 'report',
      component: () => import('../views/ReportView.vue'),
      props: true
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      // 复用首页（HomeView 已在文件顶部静态导入，这里不再重复动态导入）
      component: HomeView,
    },
  ],
})

// 路由守卫：检查面试状态
router.beforeEach((to, from) => {
  console.log(`路由跳转: ${from.path} -> ${to.path}`)
  if (to.meta.requiresInterview) {
    // 这里可以检查Pinia store中是否有活跃的面试
    // 暂时直接放行，实际项目中需要添加状态检查
    return undefined
  } else {
    return undefined
  }
})

// 路由错误处理
router.onError((error) => {
  console.error('路由导航错误:', error)
})

export default router
