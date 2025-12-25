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

    <!-- AI 리뷰 요약 섹션 -->
    <div class="ai-summary-section" v-if="reviewSummary">
      <div class="ai-summary-header">
        <span class="ai-badge">AI 분석</span>
        <h4>수강생 리뷰 3줄 요약</h4>
        <span v-if="reviewSummary.reliability === 'low'" class="reliability-warning">⚠️ 리뷰가 적어 정확도가 낮을 수 있어요</span>
      </div>
      
      <div class="summary-content">
        <p class="summary-text">"{{ reviewSummary.review_summary.summary }}"</p>
        
        <div class="pros-cons-grid">
          <div class="pros-box">
            <span class="box-label good">👍 장점</span>
            <ul>
              <li v-for="(pro, idx) in reviewSummary.review_summary.pros" :key="idx">{{ pro }}</li>
            </ul>
          </div>
          <div class="cons-box">
            <span class="box-label bad">👎 단점</span>
            <ul>
              <li v-for="(con, idx) in reviewSummary.review_summary.cons" :key="idx">{{ con }}</li>
            </ul>
          </div>
        </div>
      </div>
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
import { getCourseReviews, getReviewSummary } from '@/api/courses';
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
// Pinia getter는 자동 언래핑되므로 .value 제거
const isLoggedIn = computed(() => authStore.isAuthenticated);

const reviews = ref([]);
const reviewSummary = ref(null); // AI 요약 데이터
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

const fetchReviewSummary = async () => {
  try {
    const res = await getReviewSummary(props.courseId);
    reviewSummary.value = res.data;
  } catch (error) {
    console.error("리뷰 요약 로드 실패:", error);
    // 실패해도 전체 UI를 깨뜨리지 않음
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
    fetchReviewSummary(); // 요약도 갱신 시도
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
      fetchReviewSummary(); // 요약도 갱신 시도
    } catch (error) {
      alert('삭제 처리 중 오류가 발생했습니다.');
    }
  }
};


onMounted(() => {
  fetchReviews();
  fetchReviewSummary();
});
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

/* AI Summary Styles */
.ai-summary-section {
  background-color: #f8f9fa;
  margin: 20px 32px;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.ai-summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.ai-badge {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  font-size: 11px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 4px;
}

.ai-summary-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
}

.reliability-warning {
  font-size: 12px;
  color: #d97706;
  background: #fef3c7;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: auto;
}

.summary-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-main);
  margin-bottom: 20px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #eee;
}

.pros-cons-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.pros-box, .cons-box {
  background: white;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #eee;
}

.box-label {
  display: inline-block;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.box-label.good { color: #15803d; background: #dcfce7; }
.box-label.bad { color: #b91c1c; background: #fee2e2; }

.pros-box ul, .cons-box ul {
  margin: 0;
  padding-left: 20px;
}

.pros-box li, .cons-box li {
  font-size: 14px;
  color: var(--text-sub);
  margin-bottom: 6px;
}

@media (max-width: 768px) {
  .pros-cons-grid {
    grid-template-columns: 1fr;
  }
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