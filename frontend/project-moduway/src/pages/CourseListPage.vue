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
        <div class="filter-group">
          <h3>분야별</h3>
          <ul>
            <li v-for="cat in categories" :key="cat">
              <label>
                <input type="checkbox" :value="cat" v-model="selectedCategories">
                {{ cat }}
              </label>
            </li>
          </ul>
        </div>
        
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
      </aside>

      <!-- 메인 컨텐츠 -->
      <main class="content">
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

        <!-- 로딩 상태 -->
        <div v-if="isLoading" class="loading-state">
          <p>강좌 목록을 불러오는 중...</p>
        </div>

        <!-- 강좌 리스트 -->
        <div v-else-if="courses.length > 0" class="course-grid">
          <CourseCard
            v-for="course in courses"
            :key="course.id"
            v-bind="course"
          />
        </div>

        <!-- 빈 상태 -->
        <div v-else class="empty-state">
          <p>강좌가 없습니다.</p>
        </div>

        <!-- 페이지네이션 (Mock) -->
        <div class="pagination">
          <button class="page-btn active">1</button>
          <button class="page-btn">2</button>
          <button class="page-btn">3</button>
          <button class="page-btn">Next</button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';
import { getCourseList, searchSemanticCourses } from '@/api/courses';

const searchQuery = ref('');
const selectedCategories = ref([]);
const selectedStatuses = ref([]);
const sortBy = ref('latest');
const isLoading = ref(false);

const categories = [
  '인문', '사회', '교육', '공학', '자연', '의약', '예체능', '융·복합', '기타'
];

const statusOptions = ['접수중', '개강임박', '상시', '종료'];

// 강좌 목록 및 총 개수
const courses = ref([]);
const totalCount = ref(0);

// 초기 로딩: 평점 높은 순으로 인기 강좌 표시
const loadInitialCourses = async () => {
  isLoading.value = true;
  try {
    const { data } = await getCourseList({
      ordering: '-average_rating',  // 평점 높은 순 (기본값)
      page_size: 6  // 한 페이지에 6개씩 (성능 개선)
    });

    courses.value = data.results || [];
    totalCount.value = data.count || 0;
  } catch (error) {
    console.error("강좌 목록 로딩 실패:", error);
    alert("강좌 목록을 불러오는 중 오류가 발생했습니다.");
  } finally {
    isLoading.value = false;
  }
};

// 컴포넌트 마운트 시 초기 데이터 로드
onMounted(() => {
  loadInitialCourses();
});

const handleSearch = async () => {
  const query = searchQuery.value.trim();
  if (!query) {
    alert("검색어를 입력해주세요.");
    return;
  }

  isLoading.value = true;
  try {
    const { data } = await searchSemanticCourses(query);
    courses.value = data;
  } catch (error) {
    console.error("검색 실패:", error);
    alert("검색 중 오류가 발생했습니다.");
  } finally {
    isLoading.value = false;
  }
};
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
.sidebar { width: 220px; flex-shrink: 0; }
.filter-group { margin-bottom: 30px; }
.filter-group h3 { font-size: 18px; font-weight: 700; margin-bottom: 15px; border-bottom: 2px solid var(--text-main); padding-bottom: 10px; }
.filter-group ul li { margin-bottom: 10px; }
.filter-group label { cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 15px; color: var(--text-sub); }
.filter-group input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--primary); }
.filter-group label:hover { color: var(--primary); }

/* Main Content */
.content { flex: 1; }
.list-control { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
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

.pagination { display: flex; justify-content: center; gap: 5px; }
.page-btn { width: 36px; height: 36px; border: 1px solid var(--border); background: white; border-radius: 4px; cursor: pointer; font-weight: 600; color: var(--text-sub); transition: 0.3s; }
.page-btn:hover, .page-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
</style>