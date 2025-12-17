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
          <span class="total-count">총 <strong>{{ courses.length }}</strong>개의 강좌</span>
          <div class="sort-options">
            <select v-model="sortBy">
              <option value="latest">최신순</option>
              <option value="popular">인기순</option>
              <option value="rating">평점순</option>
            </select>
          </div>
        </div>

        <!-- 강좌 리스트 -->
        <div class="course-grid">
          <CourseCard
            v-for="course in courses"
            :key="course.id"
            v-bind="course"
          />
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
import { ref } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';

const searchQuery = ref('');
const selectedCategories = ref([]);
const selectedStatuses = ref([]);
const sortBy = ref('latest');

const categories = [
  '인문', '사회', '교육', '공학', '자연', '의약', '예체능', '융·복합', '기타'
];

const statusOptions = ['접수중', '개강임박', '상시', '종료'];

// Mock Data
const courses = ref([
  {
    id: 1,
    title: '파이썬을 활용한 빅데이터 분석 기초',
    university: '서울대학교',
    instructor: '김교수 외 1명',
    period: '15주 과정',
    status: '접수중',
    badgeColor: 'var(--primary-dark)',
  },
  {
    id: 2,
    title: '인공지능의 윤리적 쟁점과 미래 사회',
    university: 'KAIST',
    instructor: '이박사',
    period: '자율 수강',
    status: '상시',
    badgeColor: '#333',
  },
  {
    id: 3,
    title: '현대인을 위한 심리학 개론: 마음 챙김',
    university: '고려대학교',
    instructor: '박교수',
    period: '8주 과정',
    status: '마감임박',
    badgeColor: 'var(--primary-dark)',
  },
  {
    id: 4,
    title: '누구나 쉽게 배우는 핀테크 입문',
    university: 'K-MOOC 제휴',
    instructor: '금융기관',
    period: '6주 과정',
    status: 'NEW',
    badgeColor: 'var(--primary-dark)',
  },
  {
    id: 5,
    title: '디지털 마케팅의 이해와 실습',
    university: '연세대학교',
    instructor: '최교수',
    period: '12주 과정',
    status: '접수중',
    badgeColor: 'var(--primary-dark)',
  },
  {
    id: 6,
    title: '생활 속의 통계학',
    university: '부산대학교',
    instructor: '정교수',
    period: '10주 과정',
    status: '상시',
    badgeColor: '#333',
  },
]);

const handleSearch = () => {
  console.log('Search:', searchQuery.value);
  // 추후 검색 API 연동
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