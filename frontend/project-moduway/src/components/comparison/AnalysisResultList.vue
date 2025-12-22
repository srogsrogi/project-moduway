<template>
  <div class="result-list-container">
    
    <!-- Case 1: 분석 완료 후 (결과 표시) -->
    <template v-if="isAnalyzed">
      <!-- AI Comment Box -->
      <div v-if="aiComment" class="ai-comment-box">
        <div class="comment-content">
          <div class="comment-header">
            <span class="pulse-dot"></span>
            <span class="comment-label">AI 맞춤 코멘트</span>
          </div>
          <p class="comment-text">"{{ aiComment }}"</p>
          <p class="comment-note">※ AI 분석은 참고용이며 최종 결정은 학습자의 판단이 필요합니다.</p>
        </div>
      </div>

      <!-- Cards Grid -->
      <div class="cards-grid">
        <AnalysisResultCard
          v-for="res in results"
          :key="res.id"
          :result="res"
          :criteria="criteria"
        />
      </div>
    </template>

    <!-- Case 2: 분석 전 (사용 가이드) -->
    <div v-else class="guide-container">
      <div class="guide-header">
        <h2>AI 강좌 분석 사용 가이드</h2>
        <p>복잡한 강좌 선택, AI가 나에게 딱 맞는 최적의 강좌를 추천해 드립니다.</p>
      </div>

      <div class="steps-grid">
        <div class="step-item">
          <div class="step-num">1</div>
          <div class="step-content">
            <h3>관심강좌 등록</h3>
            <p>비교하고 싶은 강의를 먼저 <strong>관심강좌</strong>(위시리스트)로 등록해 주세요.</p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">2</div>
          <div class="step-content">
            <h3>학습 목표 설정</h3>
            <p>좌측 패널에 <strong>주당 학습 가능 시간</strong>과 구체적인 <strong>학습 목표</strong>를 입력하세요.</p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">3</div>
          <div class="step-content">
            <h3>중요도 조절</h3>
            <p>나에게 중요한 기준(실무, 이론 등)의 가중치를 조절해 <strong>총합 100%</strong>를 맞춰주세요.</p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">4</div>
          <div class="step-content">
            <h3>학습 성향 선택</h3>
            <p>이론 중심인지 실습 중심인지 본인의 <strong>학습 스타일</strong>을 선택하세요.</p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">5</div>
          <div class="step-content">
            <h3>비교 대상 선택</h3>
            <p>관심강좌에 등록돼 있는 강좌들 중에서 비교할 <strong>2~3개를 체크</strong>하세요.</p>
          </div>
        </div>

        <div class="step-item highlight">
          <div class="step-num">6</div>
          <div class="step-content">
            <h3>분석 시작</h3>
            <p>모든 설정이 완료되었다면 좌측 하단의 <strong>[AI 강좌 비교 분석 시작]</strong> 버튼을 클릭하세요!</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import AnalysisResultCard from './AnalysisResultCard.vue';

defineProps({
  results: {
    type: Array,
    required: true
  },
  aiComment: {
    type: String,
    default: ''
  },
  criteria: {
    type: Array,
    required: true
  },
  isAnalyzed: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.result-list-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* AI Comment Box */
.ai-comment-box {
  background: var(--bg-light);
  border: 1px solid #ffdce0;
  border-radius: 16px;
  padding: 32px;
  position: relative;
  overflow: hidden;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.pulse-dot {
  width: 8px; height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.7; }
  50% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.7; }
}
.comment-label {
  font-size: 11px;
  font-weight: 800;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.comment-text {
  font-size: 18px;
  font-weight: 700;
  color: #111;
  line-height: 1.6;
}
.comment-note {
  font-size: 11px;
  color: #888;
  margin-top: 16px;
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
}
@media (min-width: 1280px) {
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Guide Container (New) */
.guide-container {
  background: white;
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
}

.guide-header h2 {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 10px;
}
.guide-header p {
  color: var(--text-sub);
  font-size: 16px;
  margin-bottom: 40px;
}

.steps-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
  text-align: left;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 12px;
  transition: 0.2s;
}
.step-item:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-2px);
}
.step-item.highlight {
  background: #fff0f2;
  border: 1px solid #ffdce0;
}

.step-num {
  width: 28px; height: 28px;
  background: var(--text-main);
  color: white;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}
.step-item.highlight .step-num {
  background: var(--primary);
}

.step-content h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 6px;
}
.step-content p {
  font-size: 13px;
  color: var(--text-sub);
  line-height: 1.5;
  margin: 0;
}
.step-content strong {
  color: var(--primary-dark);
}
</style>