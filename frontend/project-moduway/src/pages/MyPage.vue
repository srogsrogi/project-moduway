<template>
  <div class="mypage-main">
    <div class="mypage-container">

      <div class="user-welcome">
        <h1>안녕하세요, 김싸피님!</h1>
        <p>ssafy@email.com</p>
        <div class="user-status-tag">취업 준비</div>
      </div>

      <div class="tab-nav">
        <a href="#" :class="{ active: currentTab === 'learning-status' }" @click.prevent="currentTab = 'learning-status'">학습 현황</a>
        <a href="#" :class="{ active: currentTab === 'custom-setting' }" @click.prevent="currentTab = 'custom-setting'">관심 분야 설정</a> 
        <a href="#" :class="{ active: currentTab === 'community-activity' }" @click.prevent="currentTab = 'community-activity'">커뮤니티</a>
        <a href="#" :class="{ active: currentTab === 'my-account' }" @click.prevent="currentTab = 'my-account'">내 계정</a>
      </div>

      <LearningStatusTab v-if="currentTab === 'learning-status'" />
      <CustomSettingTab v-if="currentTab === 'custom-setting'" />
      <CommunityActivityTab v-if="currentTab === 'community-activity'" />
      <MyAccountTab v-if="currentTab === 'my-account'" />

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import LearningStatusTab from '@/components/mypage/LearningStatusTab.vue';
import CustomSettingTab from '@/components/mypage/CustomSettingTab.vue';
import CommunityActivityTab from '@/components/mypage/CommunityActivityTab.vue';
import MyAccountTab from '@/components/mypage/MyAccountTab.vue'; // Need to create this one

const currentTab = ref('learning-status');
</script>

<style scoped>
/* 마이페이지 레이아웃 */
.mypage-main { padding: 40px 0; display: flex; justify-content: center; }
.mypage-container { width: 100%; max-width: 900px; padding: 0 20px; }

.user-welcome { text-align: center; padding: 20px 0; margin-bottom: 20px; }
.user-welcome h1 { font-size: 28px; font-weight: 800; margin-bottom: 5px; }
.user-welcome p { font-size: 16px; color: var(--text-sub); margin-bottom: 15px; }
.user-status-tag { display: inline-block; background-color: #e6f7ff; color: #1890ff; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 13px; }

/* 탭 내비게이션 */
.tab-nav { display: flex; border-bottom: 2px solid var(--border); margin-bottom: 30px; }
.tab-nav a { flex-grow: 1; text-align: center; padding: 15px 10px; font-size: 16px; font-weight: 600; color: var(--text-sub); border-bottom: 3px solid transparent; margin-bottom: -2px; transition: 0.2s; cursor: pointer; }
.tab-nav a.active { color: var(--primary-dark); border-bottom-color: var(--primary); font-weight: 700; }
</style>