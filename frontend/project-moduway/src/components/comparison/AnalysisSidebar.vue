<template>
  <aside class="analysis-sidebar">
    <div class="sticky-wrapper">
      
      <!-- 1. 학습 목표 및 시간 -->
      <section class="panel goal-panel">
        <div class="panel-deco-bar"></div>
        <h2 class="panel-title">
          <span class="dot"></span> 01. 학습 목표 및 시간
        </h2>
        
        <div class="input-group">
          <label>주당 학습 가능 시간</label>
          <div class="input-with-unit">
            <input type="number" v-model.number="localSettings.weeklyHours" min="1" placeholder="0">
            <span>시간</span>
          </div>
        </div>

        <div class="input-group">
          <label>학습 목적</label>
          <textarea 
            v-model="localSettings.userGoal" 
            rows="3" 
            placeholder="예: 데이터 분석가로 이직하고 싶어요."
          ></textarea>
        </div>
      </section>

      <!-- 2. 중요도 설정 -->
      <section class="panel">
        <h2 class="panel-title gray">02. 중요도 설정 ({{ totalWeight }}%)</h2>
        <div class="sliders">
          <div v-for="cr in localSettings.criteria" :key="cr.key" class="slider-item">
            <div class="slider-header">
              <span class="label">{{ cr.label }}</span>
              <span class="value">{{ cr.weight }}%</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="50" 
              v-model.number="cr.weight" 
              @input="limitWeights(cr)"
              class="custom-slider"
            >
          </div>
        </div>
      </section>

      <!-- 3. 학습 성향 -->
      <section class="panel">
        <h2 class="panel-title gray">03. 학습 성향</h2>
        <div class="pref-slider-wrapper">
          <div class="pref-labels">
            <span>이론 위주</span>
            <span>실습 위주</span>
          </div>
          <input 
            type="range" 
            min="0" 
            max="100" 
            v-model.number="localSettings.stylePref" 
            class="custom-slider"
          >
        </div>
      </section>

      <!-- 4. 분석 대상 강좌 선택 -->
      <section class="panel">
        <h2 class="panel-title gray" style="justify-content: space-between;">
          <span>04. 강좌 선택</span>
          <span class="count-badge">{{ comparisonStore.count }}/3</span>
        </h2>
        
        <div class="wishlist-container custom-scrollbar">
          <div 
            v-for="course in wishlist" 
            :key="course.id"
            class="wishlist-item"
            :class="{ active: comparisonStore.isAdded(course.id) }"
            @click="toggleSelection(course)"
          >
            <div class="item-header">
              <span class="org-name">{{ course.org_name }}</span>
              <div class="check-circle">
                <svg v-if="comparisonStore.isAdded(course.id)" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                </svg>
              </div>
            </div>
            <h3 class="course-name">{{ course.title }}</h3>
          </div>

          <!-- 데이터가 없을 경우 안내 -->
          <div v-if="wishlist.length === 0" class="empty-wishlist">
             위시리스트에 담긴 강좌가 없습니다.
          </div>
        </div>
      </section>

      <button @click="onAnalyze" class="btn-analyze">
        AI 강좌 비교 분석 시작
      </button>

    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useComparisonStore } from '@/stores/comparison';

const props = defineProps({
  settings: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['update:settings', 'analyze']);
const comparisonStore = useComparisonStore();

const localSettings = ref({ ...props.settings });
const maxTotalWeight = 100;

// Mock Wishlist Data (실제 API 연동 전 테스트 데이터)
// GEMINI.md의 예시 데이터를 기반으로 구성
const wishlist = ref([
  { id: 101, title: "파이썬 데이터 분석", org_name: "서울대학교" },
  { id: 102, title: "누구나 쉽게 배우는 핀테크 입문", org_name: "K-MOOC" },
  { id: 103, title: "딥러닝 이론 정석", org_name: "KAIST" },
  { id: 104, title: "실무 프롬프트 엔지니어링", org_name: "Udemy" },
  { id: 105, title: "데이터 사이언스 입문", org_name: "Coursera" },
  { id: 106, title: "자바스크립트 기초 완성", org_name: "인프런" },
  { id: 107, title: "리액트 마스터 클래스", org_name: "패스트캠퍼스" }
]);

const toggleSelection = (course) => {
  if (comparisonStore.isAdded(course.id)) {
    comparisonStore.removeItem(course.id);
  } else {
    // 이미 3개 꽉 찼고, 선택되지 않은 것을 선택하려 할 때
    if (comparisonStore.count >= 3) {
      alert("최대 3개 강좌까지 분석할 수 있습니다.");
      return;
    }
    comparisonStore.addItem(course);
  }
};

// 가중치 제한 로직
const limitWeights = (changedCr) => {
  const total = localSettings.value.criteria.reduce((s, cr) => s + cr.weight, 0);
  if (total > maxTotalWeight) {
    changedCr.weight -= (total - maxTotalWeight);
  }
};

const totalWeight = computed(() => {
  return localSettings.value.criteria.reduce((s, cr) => s + cr.weight, 0);
});

// 설정 변경 시 부모에게 알림 (깊은 감시)
watch(localSettings, (newVal) => {
  emit('update:settings', newVal);
}, { deep: true });

const onAnalyze = () => {
  if (comparisonStore.count === 0) {
    alert("분석할 강좌를 최소 1개 이상 선택해주세요.");
    return;
  }
  emit('analyze');
};
</script>

<style scoped>
.analysis-sidebar {
  /* Grid Layout 등 외부에서 제어 */
}

/* ... (Existing Styles) ... */
.sticky-wrapper {
  position: sticky;
  top: 100px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  padding-right: 5px;
}

/* 스크롤바 커스텀 */
.sticky-wrapper::-webkit-scrollbar { width: 4px; }
.sticky-wrapper::-webkit-scrollbar-thumb { background: #ddd; border-radius: 4px; }

.panel {
  background: white;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0; /* 패널 크기 축소 방지 */
}

.goal-panel {
  background: linear-gradient(to bottom, #fff0f2, #fff);
  border-color: #ffdce0;
}

.panel-deco-bar {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 4px;
  background: var(--primary);
}

.panel-title {
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--primary-dark);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.5px;
}
.panel-title.gray { color: #999; }

.count-badge {
  background: #eee;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #666;
}

.dot {
  width: 6px; height: 6px;
  background: var(--primary);
  border-radius: 50%;
  display: inline-block;
}

/* Input Styles */
.input-group { margin-bottom: 15px; }
.input-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-sub);
  margin-bottom: 8px;
}
.input-with-unit {
  display: flex;
  align-items: center;
  gap: 10px;
}
.input-with-unit span { font-size: 13px; font-weight: 700; color: #666; }

input[type="number"], textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ffdce0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: 0.2s;
  background: white;
}
input[type="number"]:focus, textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(246, 73, 89, 0.1);
}

/* Slider Styles */
.sliders { display: flex; flex-direction: column; gap: 20px; }
.slider-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}
.slider-header .label { font-weight: 700; }
.slider-header .value { font-weight: 900; color: var(--primary); }

.custom-slider {
  width: 100%;
  appearance: none;
  height: 4px;
  background: #eee;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}
.custom-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px; height: 18px;
  background: var(--primary);
  border-radius: 50%;
  border: 3px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.pref-slider-wrapper { margin-top: 10px; }
.pref-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  color: #999;
  margin-bottom: 10px;
}

/* Wishlist Selection Styles */
.wishlist-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* 3개 항목이 딱 맞게 보이도록 높이 조절 */
  max-height: 260px; 
  overflow-y: auto;
  padding-right: 6px;
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #ddd; border-radius: 4px; }

.wishlist-item {
  border: 2px solid transparent;
  background: #f9f9f9; /* var(--bg-light) */
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.wishlist-item:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.wishlist-item.active {
  border-color: var(--primary);
  background: white;
  box-shadow: 0 4px 12px rgba(246, 73, 89, 0.1);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.org-name {
  font-size: 11px;
  font-weight: 700;
  color: #999;
  text-transform: uppercase;
}

.check-circle {
  width: 18px; height: 18px;
  border-radius: 50%;
  border: 1px solid #ddd;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.wishlist-item.active .check-circle {
  background: var(--primary);
  border-color: var(--primary);
}

.check-circle svg {
  width: 12px; height: 12px;
  color: white;
}

.course-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.3;
  margin: 0;
}
.wishlist-item.active .course-name {
  color: var(--primary-dark);
}

.empty-wishlist {
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-size: 13px;
}

/* Button */
.btn-analyze {
  width: 100%;
  padding: 18px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  transition: 0.2s;
  box-shadow: 0 4px 15px rgba(246, 73, 89, 0.3);
  margin-top: 10px;
  margin-bottom: 30px;
}
.btn-analyze:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
}
</style>
