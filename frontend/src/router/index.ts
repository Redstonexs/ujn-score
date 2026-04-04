import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
    },
    {
      path: '/judge/:token',
      name: 'judgeHome',
      component: () => import('@/views/JudgeHomeView.vue'),
      props: true,
    },
    {
      path: '/judge/:token/score/:categoryId',
      name: 'scoring',
      component: () => import('@/views/ScoringView.vue'),
      props: true,
    },
    {
      path: '/manage',
      name: 'adminLogin',
      component: () => import('@/views/AdminLoginView.vue'),
    },
    {
      path: '/manage/dashboard',
      name: 'adminDashboard',
      component: () => import('@/views/AdminDashboardView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'notFound',
      component: () => import('@/views/InvalidRouteView.vue'),
    },
  ],
})

export default router