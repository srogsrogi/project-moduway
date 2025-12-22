<template>
  <div class="learning-status-tab">
    <!-- 1. 대시보드 통계 -->
    <DashboardStats />

    <!-- 2. 최근 학습 강좌 (이어듣기) -->
    <RecentCourse />

    <!-- 3. 강좌 목록 섹션 -->
    <div class="course-section">
      <div class="section-nav">
        <button @click="section = 'enrolled'" :class="{ active: section === 'enrolled' }">
          수강 중
        </button>
        <button @click="section = 'completed'" :class="{ active: section === 'completed' }">
          수강 완료
        </button>
        <button @click="section = 'wishlist'" :class="{ active: section === 'wishlist' }">
          찜한 강좌
        </button>
      </div>

      <div class="section-content">
        <EnrolledCourseList v-if="section === 'enrolled'" />
        <CompletedCourseList v-if="section === 'completed'" />
        <WishlistCourseList v-if="section === 'wishlist'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import DashboardStats from './dashboard/DashboardStats.vue';
import RecentCourse from './courses/RecentCourse.vue';
import EnrolledCourseList from './courses/EnrolledCourseList.vue';
import CompletedCourseList from './courses/CompletedCourseList.vue';
import WishlistCourseList from './courses/WishlistCourseList.vue';

const section = ref('enrolled'); // 기본으로 '수강 중' 섹션을 보여줍니다.
</script>

<style scoped>
.learning-status-tab {
  padding-top: 10px;
}
.course-section {
  margin-top: 50px;
}
.section-nav {
  display: flex;
  gap: 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 30px;
}
.section-nav button {
  padding: 10px 5px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-sub);
  background: none;
  border: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.section-nav button.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}
</style>
