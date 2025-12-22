<template>
  <div class="dashboard-stats">
    <div class="stat-card">
      <div class="value">{{ stats.enrolled_count }}</div>
      <div class="label">수강 중</div>
    </div>
    <div class="stat-card">
      <div class="value">{{ stats.completed_count }}</div>
      <div class="label">수강 완료</div>
    </div>
    <div class="stat-card">
      <div class="value">{{ stats.wishlist_count }}</div>
      <div class="label">찜한 강좌</div>
    </div>
    <div class="stat-card">
      <div class="value">{{ stats.my_review_count }}</div>
      <div class="label">작성한 수강평</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getDashboardStats } from '@/api/mypage';

const stats = ref({
  enrolled_count: 0,
  completed_count: 0,
  wishlist_count: 0,
  my_review_count: 0,
});

onMounted(async () => {
  try {
    const response = await getDashboardStats();
    stats.value = response.data;
  } catch (error) {
    console.error('대시보드 통계 정보를 가져오는데 실패했습니다:', error);
  }
});
</script>

<style scoped>
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  background-color: var(--bg-light);
  padding: 30px;
  border-radius: 12px;
  margin-bottom: 40px;
}
.stat-card {
  text-align: center;
}
.stat-card .value {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary);
}
.stat-card .label {
  font-size: 15px;
  color: var(--text-sub);
  margin-top: 5px;
}
</style>