<template>
  <RouterLink :to="computedLink" class="course-card-link">
    <div class="course-card">
      <div class="card-thumb">
        <span class="badge" :style="{ backgroundColor: badgeColor }">{{ displayStatus }}</span>

        <img
          v-if="course_image"
          :src="course_image"
          :alt="name"
          loading="lazy"
          decoding="async"
          :fetchpriority="priority"
          @error="handleImageError"
          @load="handleImageLoad"
        />
        <div v-else class="placeholder-thumb">THUMBNAIL</div>

        <!-- 로딩 중 placeholder -->
        <div v-if="course_image && imageLoading" class="image-loading">
          <div class="spinner"></div>
        </div>
      </div>
      <div class="card-body">
        <span class="uni-name">{{ org_name }}</span>
        <h3 class="course-title">{{ name }}</h3>
        <div class="course-info">
          <span>{{ formattedProfessor }}</span>
          <span>{{ displayPeriod }}</span>
        </div>
        <slot name="actions"></slot>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  // 백엔드 SimpleCourseSerializer 필드명 사용
  id: { type: [Number, String], required: true },
  name: { type: String, required: true },
  org_name: { type: String, required: true },
  professor: { type: String, required: true },
  course_image: { type: String, default: '' },

  // 날짜 필드들
  week: { type: Number, default: null },
  study_start: { type: String, default: '' },
  study_end: { type: String, default: '' },
  enrollment_start: { type: String, default: '' },
  enrollment_end: { type: String, default: '' },

  // 선택적 필드
  status: { type: String, default: '접수중' },
  badgeColor: { type: String, default: 'var(--primary-dark)' },

  // 라우팅 경로 (선택적, 없으면 강좌 상세 페이지)
  linkTo: { type: String, default: null },

  // 이미지 우선순위 (첫 3개는 'high', 나머지는 'auto')
  priority: { type: String, default: 'auto' }
});

// 이미지 로딩 상태
const imageLoading = ref(true);
const imageError = ref(false);

// 이미지 로드 완료 핸들러
const handleImageLoad = () => {
  imageLoading.value = false;
};

// 이미지 로드 에러 핸들러
const handleImageError = (e) => {
  imageLoading.value = false;
  imageError.value = true;
  console.warn(`이미지 로드 실패: ${props.course_image}`);
};

// 라우팅 경로 계산
const computedLink = computed(() => {
  return props.linkTo || `/courses/${props.id}`;
});

// period 계산
const displayPeriod = computed(() => {
  if (props.week) {
    return `${Math.floor(props.week)}주 과정`;
  } else if (props.study_start && props.study_end) {
    return `${props.study_start} ~ ${props.study_end}`;
  }
  return '기간 미정';
});

// 교수명 포맷팅 (쉼표로 구분된 경우 축약)
const formattedProfessor = computed(() => {
  if (!props.professor) return '';
  // 쉼표(,)를 기준으로 분리
  const names = props.professor.split(',');
  if (names.length > 1) {
    return `${names[0].trim()} 외 ${names.length - 1}명`;
  }
  return props.professor;
});

// 상태 표시 (현재는 그대로 사용)
const displayStatus = computed(() => props.status);
</script>

<style scoped>
.course-card-link { text-decoration: none; color: inherit; display: block; }
.course-card { background: white; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: 0.3s; position: relative; cursor: pointer; }
.course-card:hover { box-shadow: 0 10px 20px rgba(0,0,0,0.08); transform: translateY(-5px); border-color: #ffdce0; }

.card-thumb { height: 160px; background-color: #f0f0f0; position: relative; overflow: hidden; }
.card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
}

/* 이미지 로딩 중 placeholder */
.image-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 0;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.placeholder-thumb { width: 100%; height: 100%; background: #f6f6f6; display: flex; align-items: center; justify-content: center; color: #ccc; }

.badge { position: absolute; top: 12px; left: 12px; background: var(--primary-dark); color: white; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; z-index: 2; }

.card-body { padding: 20px; }
.uni-name { font-size: 13px; color: var(--text-sub); margin-bottom: 8px; display: block; }
.course-title { font-size: 18px; font-weight: 700; line-height: 1.4; margin-bottom: 12px; height: 50px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-top: 0; color: var(--text-main); }
.course-info { font-size: 13px; color: #888; display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 15px; margin-top: 15px; }
</style>