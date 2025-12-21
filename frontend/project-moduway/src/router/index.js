import { createRouter, createWebHistory } from 'vue-router'
import IndexPage from '@/pages/IndexPage.vue'
import CourseListPage from '@/pages/CourseListPage.vue'
import CourseDetailPage from '@/pages/CourseDetailPage.vue'
import MyPage from '@/pages/MyPage.vue'
import CommunityBoardPage from '@/pages/community/CommunityBoardPage.vue'
import PostWritePage from '@/pages/community/PostWritePage.vue'
import PostDetailPage from '@/pages/community/PostDetailPage.vue'
import GuidePage from '@/pages/GuidePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import SignupPage from '@/pages/SignupPage.vue'
import PreferenceSettingPage from '@/pages/PreferenceSettingPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: IndexPage,
    },
    {
      path: '/courses',
      name: 'courses',
      component: CourseListPage,
    },
    {
      path: '/courses/:id',
      name: 'course-detail',
      component: CourseDetailPage,
    },
    {
      path: '/mypage',
      name: 'mypage',
      component: MyPage,
    },
    {
      path: '/community',
      name: 'community',
      component: CommunityBoardPage,
    },
    {
      path: '/community/write',
      name: 'post-write',
      component: PostWritePage,
    },
    {
      path: '/community/write/:id',
      name: 'post-edit',
      component: PostWritePage,
    },
    {
      path: '/community/posts/:id',
      name: 'post-detail',
      component: PostDetailPage,
    },
    {
      path: '/guide',
      name: 'guide',
      component: GuidePage,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupPage,
    },
    {
      path: '/preferences',
      name: 'preferences',
      component: PreferenceSettingPage,
    },
    // 다른 라우트들은 작업하면서 추가
  ],
})

export default router