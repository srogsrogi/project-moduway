<template>
  <div class="course-list-container">
    <div v-if="courses.length > 0">
      <div class="info-banner">
        <span class="info-icon">💡</span>
        <span>이 강좌가 나에게 맞는지 궁금하신가요? 카드를 눌러 <b>AI 분석 결과</b>를 확인해보세요.</span>
      </div>
      <div class="course-grid">
        <CourseCard
          v-for="course in courses"
          :key="course.id"
          :id="course.id"
          :name="course.name"
          :professor="course.professor"
          :org_name="course.org_name"
          :course_image="course.course_image"
          :week="course.week"
          :study_start="course.study_start"
          :study_end="course.study_end"
          :linkTo="`/comparisons?courseId=${course.id}`"
        >
          <template #actions>
            <div class="card-actions-wishlist">
              <!-- stop.prevent로 카드 클릭(상세이동) 방지 -->
              <button class="btn-remove-wish" @click.stop.prevent="handleRemoveWish(course.id)">
                찜 해제
              </button>
            </div>
          </template>
        </CourseCard>
      </div>
    </div>
    <div v-else class="no-data">
      <p>찜한 강좌가 없습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getWishlist, removeWishlist } from '@/api/mypage';

const courses = ref([]);

// 찜 목록 조회
const fetchWishlist = async () => {
  try {
    const response = await getWishlist();
    const results = response.data.results || response.data;
    // WishlistSerializer 구조: { id:..., course: {...}, created_at:... }
    // course 객체만 추출하여 리스트에 담음
    courses.value = results.map(item => item.course);
  } catch (error) {
    console.error('찜한 강좌 목록을 가져오는데 실패했습니다:', error);
  }
};

// 찜 해제 핸들러
const handleRemoveWish = async (courseId) => {
  if (!confirm('정말 찜 목록에서 삭제하시겠습니까?')) return;

  try {
    await removeWishlist(courseId);
    // 삭제 성공 시 목록에서 제거
    courses.value = courses.value.filter(c => c.id !== courseId);
    alert('삭제되었습니다.');
  } catch (error) {
    console.error('찜 해제 실패:', error);
    alert('삭제 중 오류가 발생했습니다.');
  }
};

onMounted(() => {
  fetchWishlist();
});
</script>

<style scoped>
.info-banner {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  color: var(--text-main);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.info-icon {
  font-size: 16px;
}
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
  /* 부모인 RouterLink가 block 요소이므로 클릭 전파 방지가 중요 */
  position: relative; 
  z-index: 2;
}
.btn-remove-wish {
  font-size: 13px;
  padding: 6px 12px;
  color: var(--text-sub);
  border: 1px solid var(--border);
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-remove-wish:hover {
  background-color: #f1f3f5;
  color: #fa5252;
  border-color: #fa5252;
}
</style>
