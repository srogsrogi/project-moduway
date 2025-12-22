<template>
  <div class="comparison-page container">

    <main class="main-grid">
      <!-- Left Sidebar -->
      <div class="col-sidebar">
        <AnalysisSidebar 
          v-model:settings="settings" 
          @analyze="runAnalysis"
        />
      </div>

      <!-- Right Content -->
      <div class="col-content">
        <AnalysisResultList 
          :results="sortedResults"
          :ai-comment="aiComment"
          :criteria="settings.criteria"
          :is-analyzed="hasRunAnalysis"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useComparisonStore } from '@/stores/comparison';
import AnalysisSidebar from '@/components/comparison/AnalysisSidebar.vue';
import AnalysisResultList from '@/components/comparison/AnalysisResultList.vue';

const comparisonStore = useComparisonStore();
const hasRunAnalysis = ref(false);

// --- 상태 (Settings) ---
const settings = ref({
  weeklyHours: 12,
  userGoal: "비전공자이지만 데이터 분석 역량을 키워 이직하고 싶습니다.",
  stylePref: 70, // 이론 vs 실습
  criteria: [
    { key: "practical", label: "실무 활용도", weight: 40 },
    { key: "theory", label: "이론적 깊이", weight: 20 },
    { key: "difficulty", label: "학습 난이도", weight: 20 },
    { key: "trend", label: "최신 트렌드", weight: 20 }
  ]
});

const maxTotalWeight = 100;
const aiComment = ref("보유하신 역량을 활용할 수 있으면서도 실무 비중이 높은 과정을 우선 추천드립니다.");

// --- 가상 데이터 생성기 (백엔드 API 대용) ---
// 실제로는 comparisonStore.items에 있는 강좌에 분석 데이터를 입혀야 함
const enrichedCourses = ref([]);

const generateMockAnalysis = (course) => {
  // 강좌 ID를 시드로 사용하여 고정된 랜덤값 생성 (새로고침해도 점수 유지되도록)
  const seed = course.id * 12345; 
  const rand = (mod) => (seed % mod); // 단순 모의 랜덤

  return {
    ...course,
    // 없는 필드 채우기
    orgName: course.university || course.org_name || "교육기관",
    name: course.title || course.name || "강좌명",
    minHoursPerWeek: 4 + (course.id % 10),
    reviewCount: course.id * 3 + 2, // 일부는 데이터 부족(10미만) 나오게
    sentiment: 70 + (course.id % 25),
    reviewSummary: (course.id % 2 === 0) 
      ? "기초부터 탄탄하게 잡아주지만 과제가 다소 많아 가용 시간이 충분해야 합니다."
      : "입문자용으로 적합하며 가볍게 트렌드를 파악하기 좋으나 깊이는 다소 아쉽습니다.",
    scores: {
      practical: 50 + (course.id * 7 % 50),
      theory: 50 + (course.id * 3 % 50),
      difficulty: 30 + (course.id * 5 % 60),
      trend: 60 + (course.id * 2 % 40),
    }
  };
};

// 초기화: 스토어의 아이템을 가져와서 분석 데이터 입힘
onMounted(() => {
  if (comparisonStore.items.length === 0) {
    // 테스트용 더미 데이터 (비교함이 비어있을 때 보여주기 위함)
    enrichedCourses.value = [
      generateMockAnalysis({ id: 101, title: '파이썬 데이터 분석', university: '서울대학교' }),
      generateMockAnalysis({ id: 102, title: '핀테크 입문', university: 'K-MOOC' }),
    ];
  } else {
    enrichedCourses.value = comparisonStore.items.map(generateMockAnalysis);
  }
});

// --- 로직 (Computed) ---

const remainingPoints = computed(() => {
  const currentTotal = settings.value.criteria.reduce((s, cr) => s + cr.weight, 0);
  return maxTotalWeight - currentTotal;
});

const sortedResults = computed(() => {
  const totalWeight = settings.value.criteria.reduce((s, cr) => s + cr.weight, 0);
  
  return enrichedCourses.value.map(c => {
    // 가중 평균 점수 계산
    const weightedSum = settings.value.criteria.reduce((s, cr) => {
      return s + (c.scores[cr.key] * cr.weight);
    }, 0);
    
    // 100점 만점 환산
    const finalScore = totalWeight > 0 ? (weightedSum / (totalWeight * 100)) * 100 : 0;
    
    return { ...c, totalScore: finalScore };
  }).sort((a, b) => b.totalScore - a.totalScore); // 점수 높은 순 정렬
});

const runAnalysis = () => {
  alert("AI 분석 엔진이 설정을 바탕으로 정밀 분석을 시작합니다...");
  hasRunAnalysis.value = true;
};
</script>

<style scoped>
.comparison-page {
  padding-top: 40px;
  padding-bottom: 100px;
}

.page-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  border-bottom: 1px solid var(--border);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 800;
  color: var(--primary-dark);
  letter-spacing: -1px;
}
.page-header h1 span {
  font-weight: 300;
  color: #ccc;
}

.points-badge {
  background: var(--bg-light);
  padding: 8px 16px;
  border-radius: 50px;
  border: 1px solid #ffdce0;
  font-size: 13px;
  color: var(--primary);
}

/* Grid Layout */
.main-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

@media (min-width: 992px) {
  .main-grid {
    grid-template-columns: 300px 1fr;
  }
}
@media (min-width: 1200px) {
  .main-grid {
    grid-template-columns: 320px 1fr;
  }
}

.col-sidebar {
  /* Sidebar styles handled in component */
}
</style>
