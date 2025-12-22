<template>
  <div class="course-list-container">
    <div v-if="courses.length > 0" class="course-grid">
      <CourseCard
        v-for="course in courses"
        :key="course.id"
        :id="course.id"
        :title="course.name"
        :instructor="course.professor"
        :university="course.org_name"
        :thumbnail="course.course_image"
        period=" "
      >
        <template #actions>
          <div class="card-actions-wishlist">
            <button class="btn-remove-wish">찜 해제</button>
          </div>
        </template>
      </CourseCard>
    </div>
    <div v-else class="no-data">
      <p>찜한 강좌가 없습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getWishlist } from '@/api/mypage';

const courses = ref([]);

onMounted(async () => {
  try {
    const response = await getWishlist();
    // 페이지네이션 처리
    const results = response.data.results || response.data;
    
    // WishlistSerializer 구조상 { id:..., course: {...}, created_at:... } 형태이므로
    // course 객체만 추출하여 리스트에 담음
    courses.value = results.map(item => item.course);
  } catch (error) {
    console.error('찜한 강좌 목록을 가져오는데 실패했습니다:', error);
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
.card-actions-wishlist {
  margin-top: 15px;
  text-align: right;
}
.btn-remove-wish {
  font-size: 13px;
  padding: 5px 10px;
  color: var(--text-sub);
  border: 1px solid var(--border);
  background: white;
  border-radius: 4px;
  cursor: pointer;
}
</style>
