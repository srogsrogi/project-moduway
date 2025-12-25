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
            <input type="number" v-model.number="localSettings.weeklyHours" min="1" max="168" placeholder="0">
            <span>시간</span>
          </div>
        </div>

        <div class="input-group">
          <label>학습 목적</label>
          <textarea
            v-model="localSettings.userGoal"
            rows="4"
            placeholder="예: 비전공자이지만 데이터 분석가로 이직하고 싶습니다. 파이썬 기초는 있지만 실무 경험은 없어서 프로젝트 위주의 강좌를 선호합니다."
            maxlength="1000"
          ></textarea>
          <div class="char-count">{{ localSettings.userGoal.length }}/1000</div>
        </div>
      </section>

      <!-- 2. 중요도 설정 -->
      <section class="panel">
        <h2 class="panel-title gray">
          02. 중요도 설정
          <span class="info-icon" title="0: 전혀 중요하지 않음, 5: 매우 중요함">ⓘ</span>
        </h2>
        <div class="sliders">
          <div class="slider-item">
            <div class="slider-header">
              <span class="label">이론적 깊이</span>
              <span class="value">{{ localSettings.userPreferences.theory }}</span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              v-model.number="localSettings.userPreferences.theory"
              class="custom-slider"
            >
            <div class="slider-labels">
              <span>쉬움</span>
              <span>깊음</span>
            </div>
          </div>

          <div class="slider-item">
            <div class="slider-header">
              <span class="label">실무 활용도</span>
              <span class="value">{{ localSettings.userPreferences.practical }}</span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              v-model.number="localSettings.userPreferences.practical"
              class="custom-slider"
            >
            <div class="slider-labels">
              <span>이론중심</span>
              <span>실무중심</span>
            </div>
          </div>

          <div class="slider-item">
            <div class="slider-header">
              <span class="label">학습 난이도</span>
              <span class="value">{{ localSettings.userPreferences.difficulty }}</span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              v-model.number="localSettings.userPreferences.difficulty"
              class="custom-slider"
            >
            <div class="slider-labels">
              <span>쉬움</span>
              <span>어려움</span>
            </div>
          </div>

          <div class="slider-item">
            <div class="slider-header">
              <span class="label">학습 기간</span>
              <span class="value">{{ localSettings.userPreferences.duration }}</span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              v-model.number="localSettings.userPreferences.duration"
              class="custom-slider"
            >
            <div class="slider-labels">
              <span>짧음(1-4주)</span>
              <span>긺(17주+)</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. 분석 대상 강좌 선택 -->
      <section class="panel">
        <h2 class="panel-title gray" style="justify-content: space-between;">
          <span>03. 강좌 선택</span>
          <span class="count-badge">{{ comparisonStore.count }}/4</span>
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
            <h3 class="course-name">{{ course.name || course.title }}</h3>
          </div>

          <!-- 데이터가 없을 경우 안내 -->
          <div v-if="wishlist.length === 0" class="empty-wishlist">
             위시리스트에 담긴 강좌가 없습니다.
          </div>
        </div>
      </section>

      <button @click="onAnalyze" class="btn-analyze" :disabled="isAnalyzing">
        <span v-if="!isAnalyzing">AI 강좌 비교 분석 시작</span>
        <span v-else>분석 중...</span>
      </button>

    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useComparisonStore } from '@/stores/comparison';
import { getWishlist } from '@/api/mypage';

const props = defineProps({
  settings: {
    type: Object,
    required: true
  },
  isAnalyzing: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:settings', 'analyze']);
const comparisonStore = useComparisonStore();

const localSettings = ref({ ...props.settings });

// 위시리스트 데이터
const wishlist = ref([]);

const fetchWishlist = async () => {
  try {
    const { data } = await getWishlist();
    
    // 다른 컴포넌트와 동일한 데이터 처리 패턴 (if-else)
    let items = [];
    if (data.results) {
      items = data.results;
    } else {
      items = data;
    }

    // 배열인지 확인 후 매핑
    if (Array.isArray(items)) {
      wishlist.value = items.map(item => item.course);
    } else {
      wishlist.value = [];
    }
  } catch (error) {
    console.error("위시리스트 불러오기 실패:", error);
    // 로그인하지 않은 경우 등 에러 발생 시 빈 목록 유지
  }
};

const toggleSelection = (course) => {
  if (comparisonStore.isAdded(course.id)) {
    comparisonStore.removeItem(course.id);
  } else {
    // 이미 4개 꽉 찼고, 선택되지 않은 것을 선택하려 할 때
    if (comparisonStore.count >= 4) {
      alert("최대 4개 강좌까지 분석할 수 있습니다.");
      return;
    }
    comparisonStore.addItem(course);
  }
};

// 설정 변경 시 부모에게 알림 (깊은 감시)
watch(localSettings, (newVal) => {
  emit('update:settings', newVal);
}, { deep: true });

const onAnalyze = () => {
  if (comparisonStore.count === 0) {
    alert("분석할 강좌를 최소 1개 이상 선택해주세요.");
    return;
  }

  // 학습 목표 검증 (최소 10자)
  if (localSettings.value.userGoal.trim().length < 10) {
    alert("학습 목적을 최소 10자 이상 입력해주세요.");
    return;
  }

  emit('analyze');
};

onMounted(() => {
  fetchWishlist();
});
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

.info-icon {
  font-size: 12px;
  color: #999;
  cursor: help;
  margin-left: auto;
}

.dot {
  width: 6px; height: 6px;
  background: var(--primary);
  border-radius: 50%;
  display: inline-block;
}

/* Input Styles */
.input-group { margin-bottom: 15px; }
.input-group:last-child { margin-bottom: 0; }
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
  font-family: inherit;
}
input[type="number"]:focus, textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(246, 73, 89, 0.1);
}

.char-count {
  font-size: 11px;
  color: #999;
  text-align: right;
  margin-top: 4px;
}

/* Slider Styles */
.sliders { display: flex; flex-direction: column; gap: 20px; }

.slider-item {
  padding-bottom: 8px;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}
.slider-header .label { font-weight: 700; color: #333; }
.slider-header .value {
  font-weight: 900;
  color: var(--primary);
  min-width: 20px;
  text-align: right;
}

.custom-slider {
  width: 100%;
  appearance: none;
  height: 6px;
  background: linear-gradient(to right, #ffdce0, var(--primary));
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  margin-bottom: 6px;
}
.custom-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px; height: 20px;
  background: var(--primary);
  border-radius: 50%;
  border: 3px solid white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  cursor: pointer;
}
.custom-slider::-moz-range-thumb {
  width: 20px; height: 20px;
  background: var(--primary);
  border-radius: 50%;
  border: 3px solid white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #999;
  font-weight: 600;
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
.btn-analyze:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: translateY(-2px);
}
.btn-analyze:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
