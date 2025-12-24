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
            @keyup.enter="handleSearch"
          >
          <button @click="handleSearch">검색</button>
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
        <!-- 로딩 상태 -->
        <div v-if="isLoading" class="loading-state">
          <p>강좌 목록을 불러오는 중...</p>
        </div>

        <template v-else>
          <!-- 섹션 1: 일반 검색 결과 (또는 전체 목록) -->
          <section class="search-section">
            <div class="list-control">
              <h3 v-if="searchQuery.trim()">검색 결과</h3>
              <h3 v-else>전체 강좌</h3>
              <span class="total-count">총 <strong>{{ totalCount }}</strong>개의 강좌</span>
              <div class="sort-options">
                <select v-model="sortBy">
                  <option value="latest">최신순</option>
                  <option value="popular">인기순</option>
                  <option value="rating">평점순</option>
                </select>
              </div>
            </div>

            <!-- 강좌 리스트 -->
            <div v-if="courses.length > 0" class="course-grid">
              <CourseCard
                v-for="course in courses"
                :key="course.id"
                v-bind="course"
              />
            </div>

            <!-- 빈 상태 -->
            <div v-else class="empty-state">
              <p>조건에 맞는 강좌가 없습니다.</p>
            </div>

            <!-- 페이지네이션 -->
            <div class="pagination" v-if="courses.length > 0">
              <button
                class="page-btn"
                @click="goToPreviousPage"
                :disabled="!previousPage"
              >
                이전
              </button>
              <span class="page-info">{{ currentPage }} 페이지</span>
              <button
                class="page-btn"
                @click="goToNextPage"
                :disabled="!nextPage"
              >
                다음
              </button>
            </div>
          </section>

          <!-- 섹션 2: 의미 기반 검색 결과 (검색어 있을 때만 표시) -->
          <section class="semantic-section" v-if="searchQuery.trim() && semanticCourses.length > 0">
            <div class="section-header">
              <h3>AI 추천 강좌 (의미 기반 검색)</h3>
              <p class="section-description">입력하신 검색어와 의미적으로 유사한 강좌를 추천합니다 ({{ semanticCourses.length }}개)</p>
            </div>

            <div class="course-grid">
              <CourseCard
                v-for="course in semanticCourses"
                :key="'semantic-' + course.id"
                v-bind="course"
              />
            </div>
          </section>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getCourseList, searchSemanticCourses } from '@/api/courses';

// 검색 및 필터 상태
const searchQuery = ref('');
const selectedCategory = ref('');  // 단일 선택으로 변경
const selectedMiddleCategories = ref([]);
const selectedStatuses = ref([]);
const orgNameFilter = ref('');
const professorFilter = ref('');
const sortBy = ref('rating');
const isLoading = ref(false);
const currentPage = ref(1);

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

// 강좌 목록 및 총 개수
const courses = ref([]);
const semanticCourses = ref([]);  // 의미 기반 검색 결과
const totalCount = ref(0);
const nextPage = ref(null);
const previousPage = ref(null);

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
    // URLSearchParams는 배열을 자동으로 반복해서 전송
    // middle_classfy_name=A&middle_classfy_name=B 형태로 전송됨
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

// 강좌 목록 조회
const loadCourses = async (resetPage = false) => {
  if (resetPage) currentPage.value = 1;

  isLoading.value = true;
  try {
    const params = {
      ...buildFilterParams(),
      ordering: sortByMapping[sortBy.value],
      page: currentPage.value,
      page_size: 12
    };

    // 검색어는 search 파라미터로 전송 (의미 검색과 다름)
    if (params.query) {
      params.search = params.query;
      delete params.query;
    }

    const { data } = await getCourseList(params);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data.results || []);

    courses.value = filteredCourses;
    totalCount.value = data.count || 0;
    nextPage.value = data.next;
    previousPage.value = data.previous;
  } catch (error) {
    console.error("강좌 목록 로딩 실패:", error);
    alert("강좌 목록을 불러오는 중 오류가 발생했습니다.");
  } finally {
    isLoading.value = false;
  }
};

// 의미 기반 검색 (검색어 있을 때만, 필터 적용)
const loadSemanticCourses = async () => {
  const query = searchQuery.value.trim();
  if (!query) {
    semanticCourses.value = [];
    return;
  }

  try {
    // 필터 파라미터 포함해서 전송
    const params = buildFilterParams();
    const { data } = await searchSemanticCourses(params);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data || []);
    semanticCourses.value = filteredCourses;
  } catch (error) {
    console.error("의미 검색 실패:", error);
    semanticCourses.value = [];
  }
};

// 검색 처리
const handleSearch = async () => {
  const query = searchQuery.value.trim();
  if (!query) {
    alert("검색어를 입력해주세요.");
    return;
  }

  currentPage.value = 1;
  isLoading.value = true;

  // 일반 검색과 의미 검색 동시 실행
  await Promise.all([
    loadCourses(true),
    loadSemanticCourses()
  ]);

  isLoading.value = false;
};

// 페이지네이션
const goToNextPage = () => {
  if (nextPage.value) {
    currentPage.value++;
    loadCourses();
  }
};

const goToPreviousPage = () => {
  if (previousPage.value && currentPage.value > 1) {
    currentPage.value--;
    loadCourses();
  }
};

// Debounce 타이머
let debounceTimer = null;

// 대분류 변경 시 중분류 초기화
watch(selectedCategory, () => {
  selectedMiddleCategories.value = [];
});

// 즉시 적용 필터 (체크박스, 라디오, 셀렉트)
watch([selectedCategory, selectedMiddleCategories, selectedStatuses, sortBy], () => {
  loadCourses(true);
  // 검색어가 있으면 의미 검색도 재실행
  if (searchQuery.value.trim()) {
    loadSemanticCourses();
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
    loadCourses(true);
    // 검색어가 있으면 의미 검색도 재실행
    if (searchQuery.value.trim()) {
      loadSemanticCourses();
    }
  }, 500);
}, { deep: true });

// 컴포넌트 마운트 시 초기 데이터 로드
onMounted(() => {
  loadCourses();
});
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

/* Section Styling */
.search-section {
  margin-bottom: 60px;
}

.semantic-section {
  margin-top: 80px;
  padding-top: 40px;
  border-top: 3px solid var(--bg-light);
}

.section-header {
  margin-bottom: 25px;
}

.section-header h3 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 8px;
}

.section-description {
  font-size: 14px;
  color: var(--text-sub);
}

.list-control {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.list-control h3 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main);
}

.total-count { font-size: 15px; color: var(--text-sub); }
.total-count strong { color: var(--primary); }
.sort-options select { padding: 8px 12px; border: 1px solid var(--border); border-radius: 4px; outline: none; font-size: 14px; cursor: pointer; }

.course-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }

/* Loading & Empty State */
.loading-state, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-sub);
  font-size: 16px;
}

.loading-state p::before {
  content: '⏳ ';
}

.empty-state p::before {
  content: '📭 ';
}

/* Responsive Grid */
@media (max-width: 1024px) {
  .course-grid { grid-template-columns: repeat(2, 1fr); }
  .layout-container { flex-direction: column; }
  .sidebar { width: 100%; margin-bottom: 20px; }
  .filter-group { display: inline-block; vertical-align: top; margin-right: 30px; width: 45%; }
}
@media (max-width: 768px) {
  .course-grid { grid-template-columns: 1fr; }
  .filter-group { display: block; width: 100%; }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 40px;
}

.page-btn {
  padding: 10px 20px;
  border: 1px solid var(--border);
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  color: var(--text-sub);
  transition: 0.3s;
}

.page-btn:hover:not(:disabled) {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  padding: 0 10px;
}
</style>