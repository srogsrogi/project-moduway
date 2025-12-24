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
          <div class="card-actions completed">
            <span>수강 완료</span>
            <button class="btn-review">수강평 작성</button>
          </div>
        </template>
      </CourseCard>
    </div>
    <div v-else class="no-data">
      <p>수강 완료한 강좌가 없습니다.</p>
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
    const response = await getMyCourses('completed');
    if (response.data.results) {
        courses.value = response.data.results;
    } else {
        courses.value = response.data;
    }
  } catch (error) {
    console.error('완료한 강좌 목록을 가져오는데 실패했습니다:', error);
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
.card-actions.completed {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  width: 100%;
}
.card-actions span {
  font-weight: 600;
  color: var(--primary);
}
.btn-review {
  font-size: 13px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  background: white;
  border-radius: 4px;
  cursor: pointer;
}
</style>
