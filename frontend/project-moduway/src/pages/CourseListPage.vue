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

          <div v-if="isLoading" class="loading-state"><p>{{ loadingMessage }}</p></div>
          <div v-else-if="courses.length > 0" class="course-grid">
            <CourseCard
              v-for="(course, index) in courses"
              :key="course.id"
              v-bind="course"
              :priority="index < 3 ? 'high' : 'auto'"
            />
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
                <CourseCard
                  v-for="(course, index) in keywordCourses"
                  :key="course.id"
                  v-bind="course"
                  :priority="index < 3 ? 'high' : 'auto'"
                />
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
                <CourseCard
                  v-for="(course, index) in semanticDisplayData"
                  :key="course.id"
                  v-bind="course"
                  :priority="index < 3 ? 'high' : 'auto'"
                />
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import CourseCard from '@/components/common/CourseCard.vue';
import { getCourseList, searchKeywordCourses, searchSemanticCourses } from '@/api/courses';

const route = useRoute();

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
const loadingMessage = ref('강좌 목록을 불러오는 중...');

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

// AbortController 관리 (요청 타입별로 분리)
const abortControllers = {
  initialLoad: null,    // 목록 모드 전용
  search: null,         // 검색 모드 전용 (키워드+의미 묶음)
  prefetch: null        // 백그라운드 프리페칭 전용
};

// 캐싱 시스템
const CACHE_TTL = 5 * 60 * 1000; // 5분 (백엔드와 동일)

const cache = reactive({
  initialList: new Map(),  // key: filterHash → value: CacheEntry
  keyword: new Map(),      // key: searchHash → value: CacheEntry
  semantic: new Map()      // key: searchHash → value: CacheEntry
});

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

// 캐시 키 생성 (필터 조합을 해시화)
const generateCacheKey = (params) => {
  return JSON.stringify(
    Object.keys(params)
      .sort()
      .reduce((acc, key) => {
        acc[key] = params[key];
        return acc;
      }, {})
  );
};

// 캐시 검증 (TTL 확인)
const isValidCache = (entry) => {
  if (!entry) return false;
  const age = Date.now() - entry.timestamp;
  return age < CACHE_TTL;
};

// 오래된 캐시 정리 (메모리 관리)
const cleanupCache = () => {
  const now = Date.now();

  [cache.initialList, cache.keyword, cache.semantic].forEach(map => {
    for (const [key, entry] of map.entries()) {
      if (now - entry.timestamp > CACHE_TTL) {
        map.delete(key);
        console.log('[Cache Cleanup] 오래된 캐시 삭제');
      }
    }
  });
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

// 동적 배치 사이즈 계산 (필터 복잡도에 따라)
const calculateBatchSize = () => {
  const TARGET_DISPLAY = 9; // 목표 표시 개수
  let multiplier = 1;

  // 강좌 상태 필터가 활성화되어 있으면
  if (selectedStatuses.value.length > 0) {
    // 선택된 상태 개수에 따라 가중치 조정
    // 예: 4개 중 1개 선택 → 4배, 2개 선택 → 2배
    const totalStatuses = statusOptions.length; // 4개
    const selectedCount = selectedStatuses.value.length;
    multiplier = Math.ceil(totalStatuses / selectedCount);
  }

  // 중분류 필터도 고려
  if (selectedMiddleCategories.value.length > 0 &&
      availableMiddleCategories.value.length > 0) {
    const ratio = availableMiddleCategories.value.length /
                  selectedMiddleCategories.value.length;
    multiplier *= Math.min(ratio, 3); // 최대 3배까지만
  }

  // 텍스트 필터(운영기관, 교수)는 예측 불가능하므로 추가 여유
  if (orgNameFilter.value.trim() || professorFilter.value.trim()) {
    multiplier *= 2;
  }

  // 최종 배치 사이즈 (최소 9, 최대 100)
  const batchSize = Math.min(
    Math.max(Math.ceil(TARGET_DISPLAY * multiplier), 9),
    100
  );

  console.log(`[Batch Size] 계산됨: ${batchSize} (multiplier: ${multiplier.toFixed(2)})`);
  return batchSize;
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

// --- 초기 로딩 (재귀적 로딩 + 캐싱 + 프리페칭) ---
const loadInitialCourses = async (options = {}) => {
  const {
    skipCache = false,
    enablePrefetch = true,
    accumulatedData = [],  // 누적 데이터
    currentPage = initialPage.value,
    attempt = 1,           // 시도 횟수
    maxAttempts = 4        // 최대 4번 시도
  } = options;

  // 이전 요청 중단 (첫 시도에서만)
  if (attempt === 1) {
    abortControllers.initialLoad?.abort();
    abortControllers.prefetch?.abort();
    abortControllers.initialLoad = new AbortController();
  }

  // 동적 배치 사이즈 계산
  const batchSize = calculateBatchSize();

  const params = {
    ...buildFilterParams(),
    ordering: sortByMapping[sortBy.value],
    page: currentPage,
    page_size: batchSize
  };

  // 캐시 확인 (첫 시도에서만)
  if (attempt === 1 && !skipCache) {
    const cacheKey = generateCacheKey(params);
    const cached = cache.initialList.get(cacheKey);
    if (isValidCache(cached)) {
      const filtered = filterByStatus(cached.data);

      // 캐시된 데이터가 충분한지 확인
      if (filtered.length >= 9 || cached.isComplete) {
        console.log('[Cache Hit] 캐시에서 로드:', filtered.length, '개');
        courses.value = filtered.slice(0, 9);
        totalCount.value = cached.count;

        // 백그라운드 프리페칭
        if (enablePrefetch) {
          requestIdleCallback(() => prefetchNextPages(), { timeout: 2000 });
        }
        return;
      }
      // 캐시가 있지만 부족하면 → 추가 로드 필요
      console.log('[Cache Hit] 데이터 부족, 추가 로드');
    }
  }

  // 로딩 상태 설정
  if (attempt === 1) {
    isLoading.value = true;
    loadingMessage.value = '강좌 목록을 불러오는 중...';
  } else {
    loadingMessage.value = `더 많은 강좌를 찾는 중... (${attempt}/${maxAttempts})`;
  }

  let hasEnoughData = false; // finally에서도 접근 가능하도록 선언

  try {
    const { data } = await getCourseList(
      params,
      abortControllers.initialLoad.signal
    );

    // 새로 받은 데이터를 누적 데이터에 추가
    const allData = [...accumulatedData, ...(data.results || [])];

    // 필터링 적용
    const filtered = filterByStatus(allData);

    console.log(`[Attempt ${attempt}] 로드: ${data.results.length}개, 필터링 후: ${filtered.length}개, 누적: ${allData.length}개`);

    // 목표 개수 달성 여부 확인
    const TARGET = 9;
    hasEnoughData = filtered.length >= TARGET;
    const hasMorePages = currentPage < Math.ceil(data.count / batchSize);
    const canRetry = attempt < maxAttempts;

    if (!hasEnoughData && hasMorePages && canRetry) {
      // 데이터 부족 → 다음 페이지 추가 로드 (재귀)
      console.log(`[Recursive Load] 데이터 부족 (${filtered.length}/${TARGET}), 다음 페이지 로드`);

      return loadInitialCourses({
        skipCache: true,
        enablePrefetch: false, // 재귀 중에는 프리페칭 안 함
        accumulatedData: allData,
        currentPage: currentPage + 1,
        attempt: attempt + 1,
        maxAttempts
      });
    }

    // 성공: 데이터 충분하거나 더 이상 로드할 페이지 없음
    courses.value = filtered.slice(0, TARGET);
    totalCount.value = data.count || 0;

    // 캐시 저장 (모든 누적 데이터)
    const cacheKey = generateCacheKey({
      ...params,
      page: initialPage.value // 원래 페이지로 저장
    });
    cache.initialList.set(cacheKey, {
      data: allData,
      count: data.count,
      timestamp: Date.now(),
      page: currentPage,
      batchSize,
      isComplete: !hasMorePages || hasEnoughData // 완전한지 표시
    });

    console.log('[Cache Save] 캐시 저장:', allData.length, '개');

    // 프리페칭 시작 (첫 시도에서만)
    // 이미지 로딩을 방해하지 않도록 충분한 딜레이 후 시작
    if (attempt === 1 && enablePrefetch) {
      requestIdleCallback(() => {
        // 추가로 2초 대기 (이미지 로딩 완료 대기)
        setTimeout(() => prefetchNextPages(), 2000);
      }, { timeout: 3000 });
    }

  } catch (error) {
    if (error.name === 'CanceledError' || error.name === 'AbortError') {
      console.log('[Aborted] 요청 취소');
      return;
    }
    console.error("초기 로딩 실패:", error);

    // 에러 발생 시 누적된 데이터라도 표시
    if (accumulatedData.length > 0) {
      const filtered = filterByStatus(accumulatedData);
      courses.value = filtered.slice(0, 9);
    }
  } finally {
    if (attempt === 1 || !hasEnoughData) {
      isLoading.value = false;
    }
  }
};

// 프리페칭 (다음 페이지들을 백그라운드에서 로드)
const prefetchNextPages = async () => {
  const batchSize = calculateBatchSize();
  const currentPage = initialPage.value;
  const maxPage = Math.ceil(totalCount.value / batchSize);

  // 다음 2개 "배치"를 프리페칭
  const pagesToPrefetch = [currentPage + 1, currentPage + 2]
    .filter(p => p <= maxPage);

  if (pagesToPrefetch.length === 0) return;

  abortControllers.prefetch = new AbortController();

  for (const page of pagesToPrefetch) {
    const params = {
      ...buildFilterParams(),
      ordering: sortByMapping[sortBy.value],
      page,
      page_size: batchSize
    };

    const cacheKey = generateCacheKey(params);
    if (cache.initialList.has(cacheKey)) {
      console.log(`[Prefetch Skip] 페이지 ${page} 이미 캐시됨`);
      continue;
    }

    try {
      console.log(`[Prefetch] 페이지 ${page} (배치: ${batchSize})`);
      const { data } = await getCourseList(
        params,
        abortControllers.prefetch.signal
      );

      cache.initialList.set(cacheKey, {
        data: data.results,
        count: data.count,
        timestamp: Date.now(),
        page,
        batchSize,
        isComplete: true
      });

      console.log(`[Prefetch Success] 페이지 ${page}: ${data.results.length}개`);

      // 너무 빨리 요청하지 않도록 딜레이 추가 (네트워크 부하 분산)
      await new Promise(resolve => setTimeout(resolve, 500));

    } catch (error) {
      if (error.name === 'CanceledError' || error.name === 'AbortError') {
        console.log(`[Prefetch Aborted] 페이지 ${page}`);
        break;
      }
      console.error(`[Prefetch Error] 페이지 ${page}:`, error);
    }
  }
};

const changeInitialPage = (newPage) => {
  if (newPage < 1) return;

  // 페이지 번호 업데이트
  initialPage.value = newPage;

  // 캐시부터 확인
  const batchSize = calculateBatchSize();
  const params = {
    ...buildFilterParams(),
    ordering: sortByMapping[sortBy.value],
    page: newPage,
    page_size: batchSize
  };

  const cacheKey = generateCacheKey(params);
  const cached = cache.initialList.get(cacheKey);

  if (isValidCache(cached)) {
    const filtered = filterByStatus(cached.data);

    if (filtered.length >= 9) {
      // 캐시에서 즉시 표시
      console.log('[Page Change] 캐시 사용');
      courses.value = filtered.slice(0, 9);
      totalCount.value = cached.count;

      // 백그라운드 프리페칭 (다음 페이지들)
      // 이미지 로딩 우선순위를 위해 딜레이
      requestIdleCallback(() => {
        setTimeout(() => prefetchNextPages(), 1500);
      }, { timeout: 2000 });
      return;
    }
  }

  // 캐시 없거나 부족 → 새로 로드
  loadInitialCourses({ skipCache: false });
};

// requestIdleCallback polyfill (Safari 등에서 미지원)
const requestIdleCallback = window.requestIdleCallback || ((cb, opts) => {
  const start = Date.now();
  return setTimeout(() => {
    cb({
      didTimeout: false,
      timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
    });
  }, 1);
});

// 캐시 정리 타이머 ID
let cacheCleanupInterval = null;

onMounted(() => {
  // URL 쿼리 파라미터 확인 (메인페이지 등에서 넘어온 경우)
  if (route.query.category) {
    // 값이 변경되면 아래 watch가 동작하여 loadInitialCourses() 호출됨
    selectedCategory.value = route.query.category;
  } else {
    // 파라미터가 없으면 직접 로드
    loadInitialCourses();
  }

  // 주기적으로 캐시 정리 (5분마다)
  cacheCleanupInterval = setInterval(cleanupCache, CACHE_TTL);
});

// 컴포넌트 언마운트 시 정리
onUnmounted(() => {
  // 모든 진행 중인 요청 중단
  abortControllers.initialLoad?.abort();
  abortControllers.search?.abort();
  abortControllers.prefetch?.abort();

  // 캐시 정리 타이머 해제
  if (cacheCleanupInterval) {
    clearInterval(cacheCleanupInterval);
  }

  console.log('[Cleanup] 컴포넌트 언마운트 - 모든 요청 중단 및 타이머 해제');
});

// --- 검색 트리거 (키워드 + 의미 검색 동시 실행) ---
const triggerSearch = () => {
  const query = searchQuery.value.trim();
  if (!query) {
    alert("검색어를 입력해주세요.");
    return;
  }

  // 이전 요청 모두 중단
  abortControllers.initialLoad?.abort();
  abortControllers.prefetch?.abort();
  abortControllers.search?.abort();

  // 검색 모드 전환
  isSearched.value = true;
  keywordPage.value = 1;
  semanticPage.value = 1;

  // 새 검색 컨트롤러 생성 (키워드+의미 공유)
  abortControllers.search = new AbortController();

  // 두 검색 동시 실행 (같은 signal 사용)
  fetchKeywordSearch(abortControllers.search.signal);
  fetchSemanticSearch(abortControllers.search.signal);
};

const clearSearch = () => {
  // 검색 요청 중단
  abortControllers.search?.abort();

  isSearched.value = false;
  searchQuery.value = '';

  // 목록 모드로 복귀
  loadInitialCourses({ skipCache: false });
};

// --- 1. 키워드 검색 (ES + Fuzzy Search, Server Pagination + 캐싱) ---
const fetchKeywordSearch = async (signal = null) => {
  // signal이 없으면 새로 생성 (페이지 변경 시)
  if (!signal) {
    abortControllers.search?.abort();
    abortControllers.search = new AbortController();
    signal = abortControllers.search.signal;
  }

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

  // 캐시 확인
  const cacheKey = generateCacheKey(params);
  const cached = cache.keyword.get(cacheKey);
  if (isValidCache(cached)) {
    console.log('[Cache Hit] 키워드 검색 캐시');
    keywordCourses.value = filterByStatus(cached.data);
    totalKeywordCount.value = cached.count;
    return;
  }

  keywordLoading.value = true;
  try {
    const { data } = await searchKeywordCourses(params, signal);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data.results || []);

    keywordCourses.value = filteredCourses;
    totalKeywordCount.value = data.count || 0;

    // 캐시 저장
    cache.keyword.set(cacheKey, {
      data: data.results,
      count: data.count,
      timestamp: Date.now(),
      page: keywordPage.value
    });

    console.log('[Cache Save] 키워드 검색 캐시 저장');

  } catch (error) {
    if (error.name === 'CanceledError' || error.name === 'AbortError') {
      console.log('[Aborted] 키워드 검색 취소됨');
      return;
    }
    console.error("키워드 검색 실패:", error);
    keywordCourses.value = [];
    totalKeywordCount.value = 0;
  } finally {
    keywordLoading.value = false;
  }
};

const changeKeywordPage = (newPage) => {
  if (newPage < 1) return;
  keywordPage.value = newPage;
  fetchKeywordSearch();
};

// --- 2. 의미 기반 검색 (Client Pagination + 캐싱) ---
const fetchSemanticSearch = async (signal = null) => {
  // signal이 없으면 새로 생성 (일반적으로는 triggerSearch에서 전달됨)
  if (!signal) {
    abortControllers.search?.abort();
    abortControllers.search = new AbortController();
    signal = abortControllers.search.signal;
  }

  // 필터 파라미터 포함해서 전송
  const params = buildFilterParams();

  // 캐시 확인
  const cacheKey = generateCacheKey(params);
  const cached = cache.semantic.get(cacheKey);
  if (isValidCache(cached)) {
    console.log('[Cache Hit] 의미 검색 캐시');
    semanticAllData.value = filterByStatus(cached.data);
    return;
  }

  semanticLoading.value = true;
  try {
    const { data } = await searchSemanticCourses(params, signal);

    // 강좌 상태 필터 적용 (프론트 처리)
    const filteredCourses = filterByStatus(data || []);
    semanticAllData.value = filteredCourses;

    // 캐시 저장
    cache.semantic.set(cacheKey, {
      data: data,
      timestamp: Date.now()
    });

    console.log('[Cache Save] 의미 검색 캐시 저장');

  } catch (error) {
    if (error.name === 'CanceledError' || error.name === 'AbortError') {
      console.log('[Aborted] 의미 검색 취소됨');
      return;
    }
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
