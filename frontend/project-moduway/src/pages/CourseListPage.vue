<template>
  <div class="course-list-page">
    <!-- 페이지 헤더 -->
    <section class="page-header">
      <div class="container">
        <h2>강좌 찾기</h2>
        <div class="search-wrapper">
          <input 
            type="text" 
            placeholder="강좌명, 대학명, 교수명을 검색해보세요"
            v-model="searchQuery"
            @keyup.enter="triggerSearch"
          >
          <button @click="triggerSearch">검색</button>
        </div>
      </div>
    </section>

    <div class="container layout-container">
      <!-- 사이드바 필터 -->
      <aside class="sidebar">
        <!-- 대분류 필터 (라디오 버튼) -->
        <div class="filter-group">
          <h3>분야별</h3>
          <ul>
            <li>
              <label>
                <input type="radio" value="" v-model="selectedCategory">
                전체
              </label>
            </li>
            <li v-for="cat in categories" :key="cat">
              <label>
                <input type="radio" :value="cat" v-model="selectedCategory">
                {{ cat }}
              </label>
            </li>
          </ul>
        </div>

        <!-- 중분류 필터 (대분류 선택 시 표시) -->
        <div class="filter-group" v-if="availableMiddleCategories.length > 0">
          <h3>세부 분야</h3>
          <ul>
            <li v-for="middle in availableMiddleCategories" :key="middle">
              <label>
                <input type="checkbox" :value="middle" v-model="selectedMiddleCategories">
                {{ middle }}
              </label>
            </li>
          </ul>
        </div>

        <!-- 강좌 상태 필터 -->
        <div class="filter-group">
          <h3>강좌 상태</h3>
          <ul>
            <li v-for="stat in statusOptions" :key="stat">
              <label>
                <input type="checkbox" :value="stat" v-model="selectedStatuses">
                {{ stat }}
              </label>
            </li>
          </ul>
        </div>

        <!-- 운영기관 필터 -->
        <div class="filter-group">
          <h3>운영기관</h3>
          <input
            type="text"
            class="filter-input"
            placeholder="예: 서울대학교"
            v-model="orgNameFilter"
          >
        </div>

        <!-- 교수명 필터 -->
        <div class="filter-group">
          <h3>교수명</h3>
          <input
            type="text"
            class="filter-input"
            placeholder="예: 김교수"
            v-model="professorFilter"
          >
        </div>
      </aside>

      <!-- 메인 컨텐츠 -->
      <main class="content">
        
        <!-- Case 1: 검색 전 (전체 목록) -->
        <div v-if="!isSearched">
          <div class="list-control">
            <span class="total-count">총 <strong>{{ totalCount }}</strong>개의 강좌</span>
            <div class="sort-options">
              <select v-model="sortBy">
                <option value="latest">최신순</option>
                <option value="popular">인기순</option>
                <option value="rating">평점순</option>
              </select>
            </div>
          </div>

          <div v-if="isLoading" class="loading-state"><p>강좌 목록을 불러오는 중...</p></div>
          <div v-else-if="courses.length > 0" class="course-grid">
            <CourseCard v-for="course in courses" :key="course.id" v-bind="course" />
          </div>
          <div v-else class="empty-state"><p>강좌가 없습니다.</p></div>
          
          <!-- 전체 목록 페이지네이션 -->
          <div class="pagination" v-if="totalCount > 9">
            <button class="page-btn" :disabled="initialPage === 1" @click="changeInitialPage(initialPage - 1)">&lt;</button>
            <span class="page-info">{{ initialPage }} / {{ Math.ceil(totalCount / 9) }}</span>
            <button class="page-btn" :disabled="initialPage >= Math.ceil(totalCount / 9)" @click="changeInitialPage(initialPage + 1)">&gt;</button>
          </div>
        </div>

        <!-- Case 2: 검색 후 (두 개의 섹션) -->
        <div v-else class="search-results">

          <button class="btn-back-all" @click="clearSearch">← 전체 목록으로 돌아가기</button>

          <!-- 섹션 1: 키워드 검색 -->
          <section class="result-section keyword-section">
            <div class="section-head">
              <h3>🔍 검색 결과</h3>
              <span class="count-badge">{{ totalKeywordCount }}건</span>
            </div>

            <div v-if="keywordLoading" class="loading-state small"><p>검색 중...</p></div>
            <div v-else-if="keywordCourses.length > 0">
              <div class="course-grid">
                <CourseCard v-for="course in keywordCourses" :key="course.id" v-bind="course" />
              </div>
              <!-- Server-side Pagination -->
              <div class="pagination" v-if="totalKeywordCount > 3">
                <button class="page-btn" :disabled="keywordPage === 1" @click="changeKeywordPage(keywordPage - 1)">&lt;</button>
                <span class="page-info">{{ keywordPage }} / {{ Math.ceil(totalKeywordCount / 3) }}</span>
                <button class="page-btn" :disabled="keywordPage >= Math.ceil(totalKeywordCount / 3)" @click="changeKeywordPage(keywordPage + 1)">&gt;</button>
              </div>
            </div>
            <div v-else class="empty-state small"><p>키워드 검색 결과가 없습니다.</p></div>
          </section>

          <!-- 섹션 2: AI 의미 기반 검색 -->
          <section class="result-section ai-section">
            <div class="section-head">
              <h3>✨ 이런 강좌는 어떠세요?</h3>
              <span class="count-badge">{{ semanticAllData.length }}건</span>
            </div>

            <div v-if="semanticLoading" class="loading-state small"><p>AI 분석 중...</p></div>
            <div v-else-if="semanticDisplayData.length > 0">
              <div class="course-grid">
                <CourseCard v-for="course in semanticDisplayData" :key="course.id" v-bind="course" />
              </div>
              <!-- Client-side Pagination -->
              <div class="pagination" v-if="semanticAllData.length > 3">
                <button class="page-btn" :disabled="semanticPage === 1" @click="semanticPage--">&lt;</button>
                <span class="page-info">{{ semanticPage }} / {{ Math.ceil(semanticAllData.length / 3) }}</span>
                <button class="page-btn" :disabled="semanticPage >= Math.ceil(semanticAllData.length / 3)" @click="semanticPage++">&gt;</button>
              </div>
            </div>
            <div v-else class="empty-state small"><p>AI 검색 결과가 없습니다.</p></div>
          </section>

        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getCourseList, searchSemanticCourses } from '@/api/courses';

const searchQuery = ref('');
const selectedCategory = ref('');  // 단일 선택으로 변경
const selectedMiddleCategories = ref([]);
const selectedStatuses = ref([]);
const orgNameFilter = ref('');
const professorFilter = ref('');
const sortBy = ref('rating');

// 상태 관리
const isSearched = ref(false);
const isLoading = ref(false);

// 전체 목록 (초기)
const courses = ref([]);
const totalCount = ref(0);
const initialPage = ref(1);

// 검색 결과 데이터
const keywordCourses = ref([]);
const totalKeywordCount = ref(0);
const keywordPage = ref(1);
const keywordLoading = ref(false);

const semanticAllData = ref([]); // 전체 데이터 (Client Pagination)
const semanticPage = ref(1);
const semanticLoading = ref(false);

// 대분류-중분류 매핑 데이터
const categoryMap = {
  '인문': ['언어·문학', '인문과학'],
  '사회': ['경영·경제', '법률', '사회과학'],
  '교육': ['교육일반', '유아교육', '특수교육', '중등교육'],
  '공학': ['건축', '토목·도시', '교통·운송', '기계·금속', '전기·전자', '정밀·에너지', '소재·재료', '컴퓨터·통신', '산업', '화공', '기타'],
  '자연': ['농림·수산', '생물·화학·환경', '수학·물리·천문·지리', '생활과학'],
  '의약': ['의료', '간호', '약학', '치료·보건'],
  '예체능': ['디자인', '응용예술', '무용·체육', '미술·조형', '연극·영화', '음악'],
  '융·복합': ['융·복합'],
  '기타': ['기타']
};

const categories = Object.keys(categoryMap);
const statusOptions = ['접수중', '개강임박', '상시', '종료'];

// 선택된 대분류에 따른 중분류 목록
const availableMiddleCategories = computed(() => {
  return selectedCategory.value ? categoryMap[selectedCategory.value] : [];
});

// 정렬 옵션 매핑
const sortByMapping = {
  'latest': '-study_start',
  'popular': '-review_count',
  'rating': '-average_rating'
};

// 날짜 기반 강좌 상태 계산
const getCourseStatus = (course) => {
  const today = new Date();
  const enrollStart = course.enrollment_start ? new Date(course.enrollment_start) : null;
  const enrollEnd = course.enrollment_end ? new Date(course.enrollment_end) : null;
  const studyEnd = course.study_end ? new Date(course.study_end) : null;

  if (studyEnd && studyEnd < today) return '종료';
  if (!enrollStart || !enrollEnd) return '상시';
  if (enrollEnd < today) return '종료';
  if (enrollStart <= today && today <= enrollEnd) {
    const daysUntilEnd = Math.ceil((enrollEnd - today) / (1000 * 60 * 60 * 24));
    if (daysUntilEnd <= 7) return '개강임박';
    return '접수중';
  }
  return '접수중';
};

// 강좌 상태 필터 적용
const filterByStatus = (courseList) => {
  if (selectedStatuses.value.length === 0) return courseList;

  return courseList.filter(course => {
    const status = getCourseStatus(course);
    return selectedStatuses.value.includes(status);
  });
};

// 공통 필터 파라미터 생성 헬퍼 함수
const buildFilterParams = () => {
  const params = {};

  // 검색어
  if (searchQuery.value.trim()) {
    params.query = searchQuery.value.trim();
  }

  // 대분류 필터
  if (selectedCategory.value) {
    params.classfy_name = selectedCategory.value;
  }

  // 중분류 필터 (다중 선택 - 배열로 전송)
  if (selectedMiddleCategories.value.length > 0) {
    params.middle_classfy_name = selectedMiddleCategories.value;
  }

  // 운영기관 필터
  if (orgNameFilter.value.trim()) {
    params.org_name = orgNameFilter.value.trim();
  }

  // 교수명 필터
  if (professorFilter.value.trim()) {
    params.professor = professorFilter.value.trim();
  }

  return params;
};

// --- 초기 로딩 ---
const loadInitialCourses = async () => {
  isLoading.value = true;
  try {
    const params = {
      ...buildFilterParams(),
      ordering: sortByMapping[sortBy.value],
      page: initialPage.value,
      page_size: 9
    };

    const { data } = await getCourseList(params);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data.results || []);

    courses.value = filteredCourses;
    totalCount.value = data.count || 0;
  } catch (error) {
    console.error("초기 로딩 실패:", error);
  } finally {
    isLoading.value = false;
  }
};

const changeInitialPage = (newPage) => {
  if (newPage < 1) return;
  initialPage.value = newPage;
  loadInitialCourses();
};

onMounted(() => {
  loadInitialCourses();
});

// --- 검색 트리거 ---
const triggerSearch = () => {
  const query = searchQuery.value.trim();
  if (!query) {
    alert("검색어를 입력해주세요.");
    return;
  }
  isSearched.value = true;

  // 상태 초기화
  keywordPage.value = 1;
  semanticPage.value = 1;

  // 두 검색 동시에 실행
  fetchKeywordSearch();
  fetchSemanticSearch();
};

const clearSearch = () => {
  isSearched.value = false;
  searchQuery.value = '';
  loadInitialCourses();
};

// --- 1. 키워드 검색 (Server Pagination) ---
const fetchKeywordSearch = async () => {
  keywordLoading.value = true;
  try {
    const params = {
      ...buildFilterParams(),
      page: keywordPage.value,
      page_size: 3
    };

    // 검색어는 search 파라미터로 전송
    if (params.query) {
      params.search = params.query;
      delete params.query;
    }

    const { data } = await getCourseList(params);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data.results || []);

    keywordCourses.value = filteredCourses;
    totalKeywordCount.value = data.count || 0;
  } catch (error) {
    console.error("키워드 검색 실패:", error);
    keywordCourses.value = [];
  } finally {
    keywordLoading.value = false;
  }
};

const changeKeywordPage = (newPage) => {
  if (newPage < 1) return;
  keywordPage.value = newPage;
  fetchKeywordSearch();
};

// --- 2. 시맨틱 검색 (Client Pagination) ---
const fetchSemanticSearch = async () => {
  semanticLoading.value = true;
  try {
    // 필터 파라미터 포함해서 전송
    const params = buildFilterParams();
    const { data } = await searchSemanticCourses(params);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data || []);
    semanticAllData.value = filteredCourses;
  } catch (error) {
    console.error("AI 검색 실패:", error);
    semanticAllData.value = [];
  } finally {
    semanticLoading.value = false;
  }
};

// 시맨틱 데이터 슬라이싱
const semanticDisplayData = computed(() => {
  const start = (semanticPage.value - 1) * 3;
  return semanticAllData.value.slice(start, start + 3);
});

// --- Watch 및 Debounce 로직 ---
let debounceTimer = null;

// 대분류 변경 시 중분류 초기화
watch(selectedCategory, () => {
  selectedMiddleCategories.value = [];
});

// 즉시 적용 필터 (체크박스, 라디오, 셀렉트)
watch([selectedCategory, selectedMiddleCategories, selectedStatuses, sortBy], () => {
  if (!isSearched.value) {
    // 전체 목록 모드
    loadInitialCourses();
  } else {
    // 검색 모드 - 검색어가 있으면 두 검색 모두 재실행
    if (searchQuery.value.trim()) {
      fetchKeywordSearch();
      fetchSemanticSearch();
    }
  }
}, { deep: true });

// Debounce 적용 필터 (텍스트 입력)
watch([orgNameFilter, professorFilter], () => {
  // 이전 타이머 취소
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // 500ms 후 실행
  debounceTimer = setTimeout(() => {
    if (!isSearched.value) {
      // 전체 목록 모드
      loadInitialCourses();
    } else {
      // 검색 모드 - 검색어가 있으면 두 검색 모두 재실행
      if (searchQuery.value.trim()) {
        fetchKeywordSearch();
        fetchSemanticSearch();
      }
    }
  }, 500);
}, { deep: true });

</script>

<style scoped>
.page-header { background: var(--bg-light); padding: 40px 0; margin-bottom: 40px; }
.page-header h2 { text-align: center; margin-bottom: 20px; font-size: 32px; font-weight: 700; }
.search-wrapper { max-width: 600px; margin: 0 auto; display: flex; gap: 10px; }
.search-wrapper input { flex: 1; padding: 15px 20px; border: 1px solid var(--border); border-radius: 4px; font-size: 16px; outline: none; }
.search-wrapper input:focus { border-color: var(--primary); }
.search-wrapper button { padding: 0 30px; background: var(--primary); color: white; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; transition: 0.3s; font-size: 16px; }
.search-wrapper button:hover { background: var(--primary-dark); }

.layout-container { display: flex; gap: 40px; margin-bottom: 80px; }

/* Sidebar */
.sidebar { width: 240px; flex-shrink: 0; }
.filter-group { margin-bottom: 30px; }
.filter-group h3 { font-size: 18px; font-weight: 700; margin-bottom: 15px; border-bottom: 2px solid var(--text-main); padding-bottom: 10px; }
.filter-group ul li { margin-bottom: 10px; }
.filter-group label { cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 15px; color: var(--text-sub); }
.filter-group input[type="checkbox"],
.filter-group input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}
.filter-group label:hover { color: var(--primary); }
.filter-group .filter-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.filter-group .filter-input:focus {
  border-color: var(--primary);
}
.filter-group .filter-input::placeholder {
  color: #999;
}

/* Main Content */
.content { flex: 1; }
.list-control { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.total-count { font-size: 15px; color: var(--text-sub); }
.total-count strong { color: var(--primary); }
.sort-options select { padding: 8px 12px; border: 1px solid var(--border); border-radius: 4px; outline: none; font-size: 14px; cursor: pointer; }

/* Grid & Layout */
.course-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }

/* Search Results Sections */
.result-section { margin-bottom: 50px; }
.section-head { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
.section-head h3 { font-size: 20px; font-weight: 800; margin: 0; color: var(--text-main); }
.ai-section .section-head h3 { color: var(--primary); }
.count-badge { background: #eee; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 700; }

.btn-back-all { background: none; border: none; color: #666; cursor: pointer; margin-bottom: 20px; font-weight: 600; text-decoration: underline; }

/* Loading & Empty State */
.loading-state, .empty-state { text-align: center; padding: 60px 20px; color: var(--text-sub); font-size: 16px; }
.loading-state.small, .empty-state.small { padding: 30px; background: #f9f9f9; border-radius: 8px; margin-bottom: 20px; }
.loading-state p::before { content: '⏳ '; }
.empty-state p::before { content: '📭 '; }

/* Pagination */
.pagination { display: flex; justify-content: center; gap: 10px; align-items: center; margin-top: 10px; }
.page-btn { width: 32px; height: 32px; border: 1px solid var(--border); background: white; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.page-info { font-size: 14px; font-weight: 600; color: #666; }
</style>
