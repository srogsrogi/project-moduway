<template>
  <div class="review-section">
    <div class="section-header">
      <div class="rating-summary">
        <span class="avg-rating">{{ averageRating.toFixed(1) }}</span>
        <div class="stars-outer">
          <div class="stars-inner" :style="{ width: (averageRating / 5) * 100 + '%' }">★★★★★</div>
          <div class="stars-bg">★★★★★</div>
        </div>
        <span class="total-count">전체 수강평 {{ reviews.length }}개</span>
      </div>
      <button v-if="!userHasReviewed" class="btn-write" @click="handleWriteClick">
        <span class="icon">✏️</span> 수강평 작성하기
      </button>
    </div>

    <div class="review-list" v-if="reviews.length > 0">
      <ReviewItem 
        v-for="review in reviews" 
        :key="review.id" 
        :review="review" 
        @edit="openEditModal"
        @delete="handleReviewDelete"
      />
    </div>
    <div v-else class="no-reviews">
      <p>아직 작성된 수강평이 없습니다.</p>
      <p class="sub">이 강좌의 첫 번째 수강평을 남겨주세요!</p>
    </div>

    <!-- 작성/수정 모달 -->
    <ReviewFormModal 
      v-if="showModal" 
      :initial-data="editingReview"
      @close="showModal = false" 
      @submit="handleReviewSubmit" 
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { getCourseReviews } from '@/api/courses';
import { saveReview, deleteReview } from '@/api/mypage';
import ReviewItem from './ReviewItem.vue';
import ReviewFormModal from './ReviewFormModal.vue';

const props = defineProps({
  courseId: {
    type: [Number, String],
    required: true
  }
});

const authStore = useAuthStore();
const isLoggedIn = computed(() => authStore.isAuthenticated.value);

const reviews = ref([]);
const showModal = ref(false);
const editingReview = ref(null);

const userHasReviewed = computed(() => {
  return reviews.value.some(review => review.is_owner);
});

const averageRating = computed(() => {
  if (reviews.value.length === 0) return 0;
  const sum = reviews.value.reduce((acc, cur) => acc + cur.rating, 0);
  return sum / reviews.value.length;
});

const fetchReviews = async () => {
  try {
    const res = await getCourseReviews(props.courseId);
    // DRF PageNumberPagination 응답 처리: { count, next, previous, results: [] }
    if (res.data && Array.isArray(res.data.results)) {
      reviews.value = res.data.results;
    } else if (Array.isArray(res.data)) {
      reviews.value = res.data;
    } else {
      reviews.value = [];
    }
  } catch (error) {
    console.error("리뷰 로드 실패:", error);
    reviews.value = [];
  }
};

const openCreateModal = () => {
  editingReview.value = null; // 새 리뷰 작성
  showModal.value = true;
};

const handleWriteClick = () => {
  if (!isLoggedIn.value) {
    if (confirm('로그인이 필요한 기능입니다. 로그인 페이지로 이동할까요?')) {
      // route.fullPath를 사용하여 로그인 후 다시 돌아오도록 설정
      window.location.href = `/login?redirect=${window.location.pathname}`;
    }
    return;
  }
  openCreateModal();
};

const openEditModal = (review) => {
  editingReview.value = { ...review }; // 수정할 리뷰 데이터 전달
  showModal.value = true;
};

const handleReviewSubmit = async (formData) => {
  try {
    await saveReview(props.courseId, formData);
    alert(editingReview.value ? '수강평이 수정되었습니다.' : '수강평이 등록되었습니다.');
    showModal.value = false;
    fetchReviews(); // 목록 새로고침
  } catch (error) {
    const errorMsg = error.response?.data?.review_text?.[0] || '요청 처리 중 오류가 발생했습니다.';
    alert(errorMsg);
  }
};

const handleReviewDelete = async (reviewId) => {
  if (confirm('수강평을 정말 삭제하시겠습니까?')) {
    try {
      await deleteReview(props.courseId);
      alert('수강평이 삭제되었습니다.');
      fetchReviews(); // 목록 새로고침
    } catch (error) {
      alert('삭제 처리 중 오류가 발생했습니다.');
    }
  }
};


onMounted(fetchReviews);
</script>

<style scoped>
.review-section {
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.section-header {
  padding: 32px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rating-summary {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avg-rating {
  font-size: 36px;
  font-weight: 900;
  color: var(--text-main);
}

.stars-outer {
  position: relative;
  font-size: 24px;
  line-height: 1;
}
.stars-inner {
  position: absolute;
  top: 0; left: 0;
  color: #ffb800;
  overflow: hidden;
  white-space: nowrap;
}
.stars-bg {
  color: #eee;
}

.total-count {
  font-size: 14px;
  color: #888;
  margin-left: 8px;
}

.btn-write {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: var(--bg-light);
  border: 1px solid var(--primary);
  color: var(--primary);
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
}
.btn-write:hover {
  background: var(--primary);
  color: white;
}

.no-reviews {
  padding: 80px 0;
  text-align: center;
  color: #999;
}
.no-reviews p { font-size: 16px; font-weight: 600; margin: 0; }
.no-reviews .sub { font-size: 14px; margin-top: 8px; }

.review-list {
  display: flex;
  flex-direction: column;
}
</style>