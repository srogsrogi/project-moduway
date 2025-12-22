<template>
  <div class="review-item" :class="{ 'my-review': review.is_owner }">
    <div class="review-header">
      <div class="user-info">
        <div class="user-avatar">{{ review.user_name?.charAt(0) || '익' }}</div>
        <div class="user-meta">
          <span class="user-name">{{ review.user_name || '익명' }}</span>
          <span class="review-date">{{ formatDate(review.created_at) }}</span>
        </div>
      </div>
      <div class="review-actions">
        <div v-if="!review.is_owner" class="star-rating">
          <span v-for="i in 5" :key="i" class="star" :class="{ active: i <= review.rating }">★</span>
          <span class="rating-num">{{ review.rating.toFixed(1) }}</span>
        </div>
        <div v-else class="owner-actions">
          <button class="btn-action" @click.stop="$emit('edit', review)">수정</button>
          <button class="btn-action btn-delete" @click.stop="$emit('delete', review.id)">삭제</button>
        </div>
      </div>
    </div>
    <div class="review-content">
      <!-- 내가 쓴 리뷰에는 별점 표시 -->
      <div v-if="review.is_owner" class="star-rating-body">
        <span v-for="i in 5" :key="i" class="star" :class="{ active: i <= review.rating }">★</span>
        <span class="rating-num">{{ review.rating.toFixed(1) }}</span>
      </div>
      <p :class="{ expanded: isExpanded }">{{ review.review_text }}</p>
      <button v-if="review.review_text?.length > 200" @click="isExpanded = !isExpanded" class="btn-more">
        {{ isExpanded ? '접기' : '더보기' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  review: {
    type: Object,
    required: true
  }
});

defineEmits(['edit', 'delete']);

const isExpanded = ref(false);

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
};
</script>

<style scoped>
.review-item {
  padding: 24px;
  background: white;
  border-bottom: 1px solid #eee;
  transition: background 0.2s;
}

.review-item.my-review {
  background-color: #f8f9fa; /* 내 리뷰일 경우 배경색 강조 */
}

.review-item:last-child {
  border-bottom: none;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: #f0f2f5;
  color: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 16px;
  border: 1px solid #eee;
}
.my-review .user-avatar {
  background: var(--primary-light);
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 700;
  color: var(--text-main);
  font-size: 15px;
}

.review-date {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.review-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.owner-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  background: none;
  border: none;
  color: #888;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-action.btn-delete {
  color: var(--danger);
}

.star-rating, .star-rating-body {
  display: flex;
  align-items: center;
  gap: 2px;
}

.star {
  color: #ddd;
  font-size: 14px;
}

.star.active {
  color: #ffb800;
}

.rating-num {
  margin-left: 6px;
  font-weight: 800;
  font-size: 14px;
  color: var(--text-main);
}

.review-content {
  color: #444;
  line-height: 1.7;
  font-size: 15px;
}

.review-content p {
  margin: 0;
  white-space: pre-line;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.star-rating-body {
  margin-bottom: 12px;
}

.review-content p.expanded {
  display: block;
  overflow: visible;
}

.btn-more {
  background: none;
  border: none;
  color: var(--primary);
  font-weight: 700;
  font-size: 13px;
  padding: 0;
  margin-top: 10px;
  cursor: pointer;
}
</style>