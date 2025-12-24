<template>
  <div class="course-list-container">
    <div v-if="courses.length > 0" class="course-grid">
      <CourseCard
        v-for="enrollment in courses"
        :key="enrollment.id"
        :id="enrollment.course.id"
        :name="enrollment.course.name"
        :professor="enrollment.course.professor"
        :org_name="enrollment.course.org_name"
        :course_image="enrollment.course.course_image"
        period=" " 
      >
        <template #actions>
          <div class="card-actions">
            <div class="progress-bar">
              <div class="fill" :style="{ width: enrollment.progress_rate + '%' }"></div>
            </div>
            <span class="progress-percent">{{ enrollment.progress_rate }}%</span>
          </div>
        </template>
      </CourseCard>
    </div>
    <div v-else class="no-data">
      <p>수강 중인 강좌가 없습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getMyCourses } from '@/api/mypage';

const courses = ref([]);

onMounted(async () => {
  try {
    const response = await getMyCourses('enrolled');
    if (response.data.results) {
        courses.value = response.data.results;
    } else {
        courses.value = response.data;
    }
  } catch (error) {
    console.error('수강 중인 강좌 목록을 가져오는데 실패했습니다:', error);
  }
});
</script>

<style scoped>
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 25px;
}
.no-data {
  text-align: center;
  padding: 50px;
  background-color: var(--bg-light);
  border-radius: 12px;
  color: var(--text-sub);
}
.card-actions {
  display: flex;
  align-items: center;
  margin-top: 15px;
  gap: 10px;
}
.progress-bar {
  flex-grow: 1;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
}
.progress-bar .fill {
  height: 100%;
  background-color: var(--primary);
  border-radius: 3px;
}
.progress-percent {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  width: 40px;
  text-align: right;
}
</style>
