<template>
  <div class="learning-course-item">
    <div class="course-info">
      <div class="course-title">{{ enrollment.course.name }}</div>
      <div class="course-date">
        수강기간: {{ formatPeriod(enrollment.course.study_start, enrollment.course.study_end) }}
      </div>
      <div class="course-meta">
        <span>{{ enrollment.course.professor }}</span>
        <span>{{ enrollment.course.org_name }}</span>
      </div>
    </div>
    <div class="course-progress">
      <span class="progress-percent">{{ Math.round(enrollment.progress_rate) }}%</span>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: enrollment.progress_rate + '%' }"></div>
      </div>
    </div>
    <div class="course-action">
      <a
        :href="enrollment.course.url"
        target="_blank"
        rel="noopener noreferrer"
        class="btn btn-primary btn-sm"
      >
        이어듣기
      </a>
      <button
        v-if="showReviewButton && enrollment.status === 'completed'"
        @click="$emit('openReview', enrollment.course.id)"
        class="btn btn-outline btn-sm"
        style="margin-top: 8px;"
      >
        수강평 작성
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  enrollment: {
    type: Object,
    required: true
  },
  showReviewButton: {
    type: Boolean,
    default: false
  }
});

defineEmits(['openReview']);

const formatPeriod = (start, end) => {
  if (!start || !end) return '상시';
  const endDate = new Date(end);
  return `~${endDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'numeric', day: 'numeric' })}`;
};
</script>

<style scoped>
.learning-course-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px dashed var(--border);
}

.learning-course-item:last-child {
  border-bottom: none;
}

.course-info {
  flex-grow: 1;
  min-width: 0;
  margin-right: 20px;
}

.course-title {
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 4px;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-date {
  font-size: 13px;
  color: var(--text-sub);
  margin-bottom: 4px;
}

.course-meta {
  font-size: 12px;
  color: #888;
  display: flex;
  gap: 10px;
}

.course-meta span::before {
  content: '·';
  margin-right: 10px;
  color: var(--border);
}

.course-meta span:first-child::before {
  content: '';
  margin: 0;
}

.course-progress {
  width: 150px;
  margin-right: 20px;
  flex-shrink: 0;
}

.course-progress .progress-bar {
  height: 6px;
  margin: 5px 0;
  background-color: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.course-progress .progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s ease;
}

.course-progress .progress-percent {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  float: right;
}

.course-action {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .learning-course-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .course-info,
  .course-progress {
    width: 100%;
    margin-right: 0;
  }

  .course-action {
    align-self: flex-end;
    width: 100%;
    text-align: right;
  }

  .course-action .btn {
    width: 100%;
  }
}
</style>
