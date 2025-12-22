<template>
  <div class="recent-course-section">
    <h3 class="section-title">최근 학습 강좌</h3>
    <div v-if="course" class="recent-course-card">
      <div class="course-info">
        <p class="course-org">{{ course.course.org_name }}</p>
        <h4 class="course-name">{{ course.course.name }}</h4>
        <div class="progress-bar">
          <div class="fill" :style="{ width: course.progress_rate + '%' }"></div>
        </div>
        <p class="progress-percent">{{ course.progress_rate }}%</p>
      </div>
      <a :href="course.continue_url" class="btn btn-primary">이어듣기</a>
    </div>
    <div v-else class="no-data">
      <p>최근 학습한 강좌가 없습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getRecentCourse } from '@/api/mypage';

const course = ref(null);

onMounted(async () => {
  try {
    const response = await getRecentCourse();
    course.value = response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      // 404 에러는 최근 학습 강좌가 없는 경우이므로 정상 처리
      course.value = null;
    } else {
      console.error('최근 학습 강좌를 가져오는데 실패했습니다:', error);
    }
  }
});
</script>

<style scoped>
.recent-course-section {
  margin-bottom: 50px;
}
.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}
.recent-course-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 25px;
  border: 1px solid var(--border);
  border-radius: 12px;
}
.course-info {
  flex-grow: 1;
  margin-right: 20px;
}
.course-org {
  font-size: 14px;
  color: var(--text-sub);
  margin-bottom: 5px;
}
.course-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
}
.progress-bar {
  height: 8px;
  background-color: var(--bg-light);
  border-radius: 4px;
  overflow: hidden;
  width: 80%;
}
.progress-bar .fill {
  height: 100%;
  background-color: var(--primary);
}
.progress-percent {
  font-size: 14px;
  color: var(--text-sub);
  margin-top: 8px;
}
.btn {
  white-space: nowrap;
}
.no-data {
  text-align: center;
  padding: 40px;
  background-color: var(--bg-light);
  border-radius: 12px;
  color: var(--text-sub);
}
</style>