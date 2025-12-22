<template>
  <div class="result-card">
    <div class="card-header">
      <div class="info-area">
        <div class="badges">
          <span class="badge org">{{ result.orgName }}</span>
          <span v-if="result.reviewCount < 10" class="badge warning">데이터 부족</span>
        </div>
        <h3 class="course-name">{{ result.name }}</h3>
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

    <div class="simulation-box">
      <div class="sim-title">🕒 타임라인 시뮬레이션</div>
      <p>
        수강 종료일까지 매주 <span class="highlight">{{ result.minHoursPerWeek }}시간</span> 이상의 학습이 권장됩니다.
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
          <span class="metric-label">분석 신뢰도</span>
          <span class="metric-value" :class="result.reviewCount > 10 ? 'high' : 'low'">
            {{ result.reviewCount > 10 ? '높음' : '주의' }}
          </span>
        </div>
      </div>

      <div class="ai-summary">
        <span class="metric-label">강좌 핵심 요약</span>
        <p>{{ result.reviewSummary }}</p>
      </div>

      <!-- 2. 세부 점수 바 차트 -->
      <div class="scores-bars">
        <div v-for="cr in criteria" :key="cr.key" class="bar-row">
          <span class="bar-label">{{ cr.label }}</span>
          <div class="bar-track-wrapper">
            <div class="bar-track">
              <div 
                class="bar-fill" 
                :style="{ width: result.scores[cr.key] + '%' }"
              ></div>
            </div>
            <span class="bar-value">{{ result.scores[cr.key] }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <button class="btn-detail">강좌 상세 정보 및 수강신청</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  criteria: {
    type: Array,
    required: true
  }
});

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

.card-header {
  padding: 32px 32px 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.info-area { flex: 1; margin-right: 20px; }

.badges { display: flex; gap: 8px; margin-bottom: 12px; }
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
}
.result-card:hover .course-name { color: var(--primary); }

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
}
.sim-title { font-size: 11px; font-weight: 700; color: #666; margin-bottom: 4px; }
.simulation-box p { font-size: 13px; font-weight: 600; color: #444; }
.highlight { color: var(--primary); }

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
.metric-value { font-size: 14px; font-weight: 700; }
.metric-value.positive { color: #10b981; }
.metric-value.high { color: #3b82f6; }
.metric-value.low { color: #f59e0b; }

.ai-summary { margin-bottom: 24px; }
.ai-summary p { font-size: 13px; color: #666; line-height: 1.6; margin-top: 4px; }

/* Bars */
.scores-bars {
  padding-top: 16px;
  border-top: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 12px;
}
.bar-row { display: flex; align-items: center; justify-content: space-between; }
.bar-label { font-size: 11px; font-weight: 500; color: #666; width: 70px; }
.bar-track-wrapper { flex: 1; display: flex; align-items: center; gap: 12px; }
.bar-track { 
  flex: 1; height: 6px; 
  background: #f3f4f6; border-radius: 3px; overflow: hidden; 
}
.bar-fill { height: 100%; background: #111; transition: width 1s ease; }
.bar-value { font-size: 11px; font-weight: 700; width: 20px; text-align: right; }

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
