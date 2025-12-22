<template>
  <RouterLink :to="`/courses/${id}`" class="course-card-link">
    <div class="course-card">
      <div class="card-thumb">
        <span class="badge" :style="{ backgroundColor: badgeColor }">{{ displayStatus }}</span>
        
        <!-- 비교함 담기 버튼 -->
        <button 
          class="btn-compare-toggle" 
          :class="{ active: isAdded }"
          @click.prevent.stop="toggleComparison"
          title="AI 분석함에 담기"
        >
          {{ isAdded ? '✓' : '+' }}
        </button>

        <img v-if="course_image" :src="course_image" :alt="name" />
        <div v-else class="placeholder-thumb">THUMBNAIL</div>
      </div>
      <div class="card-body">
        <span class="uni-name">{{ org_name }}</span>
        <h3 class="course-title">{{ name }}</h3>
        <div class="course-info">
          <span>{{ formattedProfessor }}</span>
          <span>{{ displayPeriod }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue';
import { useComparisonStore } from '@/stores/comparison';

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
  badgeColor: { type: String, default: 'var(--primary-dark)' }
});

const comparisonStore = useComparisonStore();

const isAdded = computed(() => comparisonStore.isAdded(props.id));

const toggleComparison = () => {
  if (isAdded.value) {
    comparisonStore.removeItem(props.id);
  } else {
    // 필요한 데이터만 객체로 구성해서 저장
    comparisonStore.addItem({
      id: props.id,
      name: props.name,
      org_name: props.org_name,
      professor: props.professor,
      course_image: props.course_image
    });
  }
};

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

.card-thumb { height: 160px; background-color: #eee; position: relative; overflow: hidden; }
.card-thumb img { width: 100%; height: 100%; object-fit: cover; }
.placeholder-thumb { width: 100%; height: 100%; background: #f6f6f6; display: flex; align-items: center; justify-content: center; color: #ccc; }

.badge { position: absolute; top: 12px; left: 12px; background: var(--primary-dark); color: white; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; z-index: 1; }

/* 비교함 토글 버튼 스타일 */
.btn-compare-toggle {
  position: absolute;
  top: 12px; right: 12px;
  width: 32px; height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  color: #666;
  font-size: 18px;
  cursor: pointer;
  z-index: 2;
  display: flex; align-items: center; justify-content: center;
  transition: 0.2s;
  backdrop-filter: blur(2px);
}
.btn-compare-toggle:hover {
  background: white;
  color: var(--primary);
  transform: scale(1.1);
}
.btn-compare-toggle.active {
  background: var(--primary);
  color: white;
  box-shadow: 0 2px 8px rgba(246, 73, 89, 0.4);
}

.card-body { padding: 20px; }
.uni-name { font-size: 13px; color: var(--text-sub); margin-bottom: 8px; display: block; }
.course-title { font-size: 18px; font-weight: 700; line-height: 1.4; margin-bottom: 12px; height: 50px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-top: 0; color: var(--text-main); }
.course-info { font-size: 13px; color: #888; display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 15px; margin-top: 15px; }
</style>