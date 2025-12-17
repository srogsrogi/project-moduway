<template>
  <div class="index-page">
    <!-- 메인 히어로 섹션 -->
    <section class="hero">
        <div class="container">
            <h1>언제 어디서나,<br>당신의 <span>배움</span>을 잇습니다.</h1>
            <p>국내 유수 대학의 명품 강좌를 무료로 만나보세요.</p>
            <div class="search-bar">
                <input type="text" placeholder="배우고 싶은 분야나 강좌명을 입력하세요">
                <button>🔍</button>
            </div>
        </div>
    </section>

    <!-- 카테고리 섹션 -->
    <section class="categories container">
        <div class="section-title">
            분야별 탐색
        </div>
        <div class="cate-grid">
            <div class="cate-item"><span class="cate-icon">📚</span>인문</div>
            <div class="cate-item"><span class="cate-icon">👥</span>사회</div>
            <div class="cate-item"><span class="cate-icon">🎓</span>교육</div>
            <div class="cate-item"><span class="cate-icon">⚙️</span>공학</div>
            <div class="cate-item"><span class="cate-icon">🔬</span>자연</div>
            <div class="cate-item"><span class="cate-icon">🩺</span>의약</div>
            <div class="cate-item"><span class="cate-icon">🎨</span>예체능</div>
            <div class="cate-item"><span class="cate-icon">🧩</span>융·복합</div>
            <div class="cate-item"><span class="cate-icon">✨</span>기타</div>
        </div>
    </section>

    <!-- 강좌 카드 그리드 -->
    <section class="course-list-section container">
        <div class="section-title">
            신규 & 인기 강좌
            <router-link to="/courses">전체보기 →</router-link>
        </div>

        <div class="filter-bar">
            <div class="filter-chip active">전체</div>
            <div class="filter-chip">접수중</div>
            <div class="filter-chip">개강임박</div>
            <div class="filter-chip">상시강좌</div>
            <div class="filter-chip">이수증 발급</div>
        </div>

        <div class="course-grid">
          <CourseCard
            v-for="course in courses"
            :key="course.id"
            v-bind="course"
          />
        </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import CourseCard from '@/components/common/CourseCard.vue';

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
]);
</script>

<style scoped>
/* 메인 히어로 섹션 */
.hero { padding: 80px 0; text-align: center; background: linear-gradient(180deg, #fff 0%, #fff0f2 100%); }
.hero h1 { font-size: 48px; margin-bottom: 20px; line-height: 1.3; font-weight: 700; }
.hero span { color: var(--primary); }
.hero p { color: var(--text-sub); font-size: 18px; margin-bottom: 40px; }
.search-bar { max-width: 600px; margin: 0 auto; display: flex; position: relative; }
.search-bar input { width: 100%; padding: 18px 20px; border: 2px solid var(--primary); border-radius: 50px; font-size: 16px; outline: none; }
.search-bar button { position: absolute; right: 8px; top: 8px; background: var(--primary); color: white; border: none; width: 48px; height: 48px; border-radius: 50%; cursor: pointer; font-size: 18px; }

/* 카테고리 섹션 */
.categories { padding: 60px 0; }
.section-title { font-size: 28px; font-weight: 700; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: end; }
.section-title a { font-size: 14px; color: var(--text-sub); }
.cate-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
@media (min-width: 992px) {
    .cate-grid { grid-template-columns: repeat(5, 1fr); }
}
.cate-item { background: var(--bg-light); padding: 20px 10px; text-align: center; border-radius: 12px; transition: 0.3s; cursor: pointer; border: 1px solid transparent; }
.cate-item:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-3px); }
.cate-icon { font-size: 24px; margin-bottom: 10px; display: block; }

/* 강좌 카드 그리드 */
.course-list-section { padding: 60px 0 100px; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 30px; overflow-x: auto; padding-bottom: 10px; }
.filter-chip { padding: 8px 16px; border: 1px solid var(--border); border-radius: 20px; font-size: 14px; cursor: pointer; background: white; white-space: nowrap; }
.filter-chip.active { background: var(--primary); color: white; border-color: var(--primary); }

.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; }
</style>