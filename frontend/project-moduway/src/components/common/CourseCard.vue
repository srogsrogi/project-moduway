<template>
  <RouterLink :to="`/courses/${id}`" class="course-card-link">
    <div class="course-card">
      <div class="card-thumb">
        <span class="badge" :style="{ backgroundColor: badgeColor }">{{ displayStatus }}</span>
        <img v-if="course_image" :src="course_image" :alt="name" />
        <div v-else class="placeholder-thumb">THUMBNAIL</div>
      </div>
      <div class="card-body">
        <span class="uni-name">{{ org_name }}</span>
        <h3 class="course-title">{{ name }}</h3>
        <div class="course-info">
          <span>{{ professor }}</span>
          <span>{{ displayPeriod }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // 백엔드 SimpleCourseSerializer 필드명 사용
  id: { type: [Number, String], required: true },
  name: { type: String, required: true },              // title → name
  org_name: { type: String, required: true },          // university → org_name
  professor: { type: String, required: true },         // instructor → professor
  course_image: { type: String, default: '' },         // thumbnail → course_image

  // 날짜 필드들 (period 대신 개별 필드)
  week: { type: Number, default: null },
  study_start: { type: String, default: '' },
  study_end: { type: String, default: '' },
  enrollment_start: { type: String, default: '' },
  enrollment_end: { type: String, default: '' },

  // 선택적 필드
  status: { type: String, default: '접수중' },
  badgeColor: { type: String, default: 'var(--primary-dark)' }
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

.card-body { padding: 20px; }
.uni-name { font-size: 13px; color: var(--text-sub); margin-bottom: 8px; display: block; }
.course-title { font-size: 18px; font-weight: 700; line-height: 1.4; margin-bottom: 12px; height: 50px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-top: 0; color: var(--text-main); }
.course-info { font-size: 13px; color: #888; display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 15px; margin-top: 15px; }
</style>