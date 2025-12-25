<template>
  <div class="result-card" :class="{ open: isOpen }">
    <div class="card-header">
      <div class="info-area">
        <div class="badges">
          <span class="badge org">{{ result.orgName }}</span>
          <span v-if="result.reviewCount < 10" class="badge warning">데이터 부족</span>
          <span v-if="result.reliability === 'low'" class="badge warning">신뢰도 낮음</span>
        </div>
        <h3 class="course-name">{{ result.name }}</h3>
        <p v-if="result.courseSummary" class="course-summary">{{ result.courseSummary }}</p>
      </div>

      <!-- Progress Ring (적합도 점수) -->
      <div class="score-ring">
        <svg viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" class="bg-ring" />
          <circle
            cx="40" cy="40" r="36"
            class="progress-ring"
            :style="ringStyle"
          />
        </svg>
        <div class="score-text">
          <span class="score">{{ Math.round(result.totalScore) }}</span>
          <span class="label">Match</span>
        </div>
      </div>
    </div>

    <!-- 핵심 포인트 (항상 보임) -->
    <div v-if="result.personalized_comment && result.personalized_comment.key_points" class="key-points-section">
      <div class="points-title">📌 핵심 포인트</div>
      <ul class="points-list">
        <li v-for="(point, index) in result.personalized_comment.key_points" :key="index">
          {{ point }}
        </li>
      </ul>
    </div>

    <!-- 상세 보기 토글 버튼 (접혀있을 때만 표시) -->
    <button v-if="!isOpen" class="btn-toggle-details" @click="isOpen = true">
      더 보기 ▼
    </button>

    <!-- 상세 내용 (토글됨) -->
    <div v-show="isOpen" class="details-content">
      <div class="simulation-box" :class="getTimelineStatusClass(result.timelineStatus)">
        <div class="sim-title">
          🕒 타임라인 시뮬레이션
          <span v-if="result.timelineStatus" class="status-badge">{{ result.timelineStatus }}</span>
        </div>
        <p v-if="result.timelineStatus === '종료'">
          이미 종료된 강의입니다. (수강 기간 만료)
        </p>
        <p v-else>
          수강 종료일까지 매주 <span class="highlight">{{ result.minHoursPerWeek }}시간</span> 이상의 학습이 권장됩니다.
          <template v-if="result.remainingWeeks">
            (남은 기간: {{ result.remainingWeeks }}주 / 전체 {{ result.totalWeeks }}주)
          </template>
        </p>
      </div>

      <div class="details-area">
        <!-- 1. 분석 요약 -->
        <div class="metrics-grid">
          <div class="metric">
            <span class="metric-label">긍정 리뷰 비율</span>
            <span class="metric-value positive">{{ result.sentiment }}% Positive</span>
          </div>
          <div class="metric right">
            <span class="metric-label">리뷰 개수</span>
            <span class="metric-value">{{ result.reviewCount }}개</span>
          </div>
        </div>

        <!-- 리뷰 요약 -->
        <div class="ai-summary">
          <span class="metric-label">강좌 리뷰 요약</span>
          <p class="summary-text">{{ result.reviewSummary }}</p>

          <!-- 장단점 표시 (있는 경우만) -->
          <div v-if="result.reviewPros && result.reviewPros.length > 0" class="pros-cons">
            <div class="pros">
              <div class="section-title">👍 장점</div>
              <ul>
                <li v-for="(pro, index) in result.reviewPros" :key="index">{{ pro }}</li>
              </ul>
            </div>
            <div v-if="result.reviewCons && result.reviewCons.length > 0" class="cons">
              <div class="section-title">👎 단점</div>
              <ul>
                <li v-for="(con, index) in result.reviewCons" :key="index">{{ con }}</li>
              </ul>
            </div>
          </div>

          <p v-if="result.reviewWarning" class="warning-text">⚠️ {{ result.reviewWarning }}</p>
        </div>

        <!-- 2. 세부 점수 바 차트 -->
        <div class="scores-bars">
          <div class="bar-row">
            <span class="bar-label">이론적 깊이</span>
            <div class="bar-track-wrapper">
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: result.scores.theory + '%' }"
                ></div>
              </div>
              <span class="bar-value">{{ Math.round(result.scores.theory) }}</span>
            </div>
          </div>

          <div class="bar-row">
            <span class="bar-label">실무 활용도</span>
            <div class="bar-track-wrapper">
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: result.scores.practical + '%' }"
                ></div>
              </div>
              <span class="bar-value">{{ Math.round(result.scores.practical) }}</span>
            </div>
          </div>

          <div class="bar-row">
            <span class="bar-label">학습 난이도</span>
            <div class="bar-track-wrapper">
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: result.scores.difficulty + '%' }"
                ></div>
              </div>
              <span class="bar-value">{{ Math.round(result.scores.difficulty) }}</span>
            </div>
          </div>

          <div class="bar-row">
            <span class="bar-label">학습 기간</span>
            <div class="bar-track-wrapper">
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: result.scores.duration + '%' }"
                ></div>
              </div>
              <span class="bar-value">{{ Math.round(result.scores.duration) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card-footer">
        <button class="btn-detail" @click="goToCourseDetail">강좌 상세 정보 및 수강신청</button>
      </div>

      <!-- 접기 버튼 (펼쳐졌을 때 최하단에 표시) -->
      <button class="btn-toggle-details btn-collapse" @click="isOpen = false">
        접기 ▲
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
});

const router = useRouter();
const isOpen = ref(false); // 상세 내용 펼치기 상태

// 원 둘레 길이 (r=36 -> 2 * PI * 36 ≈ 226.1)
const CIRCUMFERENCE = 226.1;

const ringStyle = computed(() => {
  const score = props.result.totalScore || 0;
  // stroke-dashoffset 계산: (1 - 퍼센트) * 둘레
  const offset = CIRCUMFERENCE * (1 - score / 100);
  return {
    strokeDasharray: CIRCUMFERENCE,
    strokeDashoffset: offset
  };
});

// 타임라인 상태별 클래스
const getTimelineStatusClass = (status) => {
  if (!status) return '';

  const statusMap = {
    '적정': 'status-optimal',
    '널널': 'status-relaxed',
    '빠듯': 'status-tight',
    '종료': 'status-finished',
    '판정불가': 'status-unknown'
  };

  return statusMap[status] || '';
};

// 강좌 상세 페이지로 이동
const goToCourseDetail = () => {
  if (props.result.id) {
    router.push(`/courses/${props.result.id}`);
  }
};
</script>

<style scoped>
.result-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 24px;
  overflow: hidden;
  transition: 0.3s;
  display: flex;
  flex-direction: column;
}
.result-card:hover {
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border-color: #ffdce0;
  transform: translateY(-5px);
}

.result-card.open {
  border-color: var(--primary);
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
}

/* Key Points Section */
.key-points-section {
  padding: 0 32px 20px 32px;
  min-height: 140px; /* 핵심 포인트 개수가 달라도 기본 카드 높이 통일 */
}

.points-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary-dark);
  margin-bottom: 8px;
  text-transform: uppercase;
}

.points-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.points-list li {
  font-size: 14px;
  color: #444;
  line-height: 1.6;
  margin-bottom: 6px;
  padding-left: 20px;
  position: relative;
}

.points-list li::before {
  content: "✔";
  position: absolute;
  left: 0;
  color: var(--primary);
  font-weight: 800;
}

/* Toggle Button */
.btn-toggle-details {
  width: 100%;
  padding: 12px;
  background: #f9fafb;
  border: none;
  border-top: 1px solid #f3f4f6;
  border-bottom: 1px solid #f3f4f6;
  color: #6b7280;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
  margin-top: auto;
}

.btn-toggle-details:hover {
  background: #f3f4f6;
  color: var(--primary);
}

/* 접기 버튼 (details-content 안에 있을 때) */
.btn-toggle-details.btn-collapse {
  margin-top: 0;
  border-top: 1px solid #f3f4f6;
  border-bottom: none;
}

.details-content {
  /* 펼침 애니메이션은 JS나 transition 컴포넌트로 처리하는게 좋지만, 여기선 단순 v-show */
  padding-top: 24px;
  padding-bottom: 0;
}

/* 기존 스타일 */
.card-header {
  padding: 32px 32px 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.info-area { flex: 1; margin-right: 20px; }

.badges { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 4px;
}
.badge.org { background: #1f2937; color: white; }
.badge.warning { background: #fef3c7; color: #b45309; }

.course-name {
  font-size: 20px;
  font-weight: 700;
  color: #111;
  line-height: 1.3;
  margin-bottom: 8px;
}
.result-card:hover .course-name { color: var(--primary); }

.course-summary {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  margin-top: 8px;
}

/* Progress Ring */
.score-ring {
  width: 80px; height: 80px;
  position: relative;
  flex-shrink: 0;
}
.score-ring svg { transform: rotate(-90deg); width: 100%; height: 100%; }
.bg-ring { fill: none; stroke: #f0f0f0; stroke-width: 6; }
.progress-ring {
  fill: none;
  stroke: var(--primary);
  stroke-width: 6;
  transition: stroke-dashoffset 1s ease-in-out;
  stroke-linecap: round;
}
.score-text {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.score-text .score { font-size: 20px; font-weight: 900; color: #111; }
.score-text .label { font-size: 9px; font-weight: 700; color: #999; text-transform: uppercase; }

/* Simulation Box */
.simulation-box {
  margin: 0 32px 24px 32px;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  transition: 0.2s;
}
.sim-title {
  font-size: 11px;
  font-weight: 700;
  color: #666;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-badge {
  background: #e5e7eb;
  color: #374151;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
}
.simulation-box p { font-size: 13px; font-weight: 600; color: #444; line-height: 1.5; }
.highlight { color: var(--primary); }

/* 타임라인 상태별 스타일 */
.status-optimal { background: #ecfdf5; border-color: #6ee7b7; }
.status-optimal .status-badge { background: #10b981; color: white; }

.status-relaxed { background: #eff6ff; border-color: #93c5fd; }
.status-relaxed .status-badge { background: #3b82f6; color: white; }

.status-tight { background: #fef3c7; border-color: #fcd34d; }
.status-tight .status-badge { background: #f59e0b; color: white; }

.status-finished { background: #f3f4f6; border-color: #d1d5db; }
.status-finished .status-badge { background: #6b7280; color: white; }

/* Details Area */
.details-area {
  padding: 0 32px 32px 32px;
  flex: 1;
}
.metrics-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;
}
.metric.right { text-align: right; }
.metric-label { display: block; font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; }
.metric-value { font-size: 14px; font-weight: 700; color: #333; }
.metric-value.positive { color: #10b981; }

.ai-summary { margin-bottom: 24px; }
.summary-text { font-size: 13px; color: #666; line-height: 1.6; margin-top: 4px; }

.pros-cons {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.section-title {
  font-size: 11px;
  font-weight: 700;
  color: #333;
  margin-bottom: 6px;
}
.pros-cons ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.pros-cons li {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 4px;
  padding-left: 12px;
  position: relative;
}
.pros li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #10b981;
}
.cons li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #ef4444;
}

.warning-text {
  font-size: 11px;
  color: #f59e0b;
  margin-top: 8px;
  font-weight: 600;
}

/* Bars */
.scores-bars {
  padding-top: 16px;
  border-top: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 12px;
}
.bar-row { display: flex; align-items: center; justify-content: space-between; }
.bar-label { font-size: 11px; font-weight: 500; color: #666; width: 80px; }
.bar-track-wrapper { flex: 1; display: flex; align-items: center; gap: 12px; }
.bar-track {
  flex: 1; height: 6px;
  background: #f3f4f6; border-radius: 3px; overflow: hidden;
}
.bar-fill { height: 100%; background: #111; transition: width 1s ease; }
.bar-value { font-size: 11px; font-weight: 700; width: 30px; text-align: right; }

/* Footer */
.card-footer {
  padding: 24px;
  background: #f9f9f9;
  border-top: 1px solid var(--border);
}
.btn-detail {
  width: 100%;
  padding: 12px;
  background: white;
  border: 1px solid var(--primary);
  color: var(--primary);
  border-radius: 8px;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  transition: 0.2s;
}
.btn-detail:hover {
  background: var(--primary);
  color: white;
}
</style>
