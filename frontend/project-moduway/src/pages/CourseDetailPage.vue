<template>
  <div class="course-detail-page" v-if="course">
    <section class="course-hero">
      <div class="container hero-content">
        <div class="hero-text">
          <div class="university-tag">{{ course.org_name }}</div>
          <h1 class="course-title">{{ course.name }}</h1>
          <p class="instructor-info">
            <strong>교수진:</strong> {{ course.professor }} | 
            <strong>분야:</strong> {{ course.classfy_name }} > {{ course.middle_classfy_name }}
          </p>
          <div class="course-stats-inline">
            <span class="rating-badge">★ {{ course.rating || '0.0' }}</span>
            <span class="vod-time">📺 VOD {{ Math.round(course.course_playtime / 60) }}분</span>
          </div>
          <div class="action-buttons">
            <button class="btn-enroll" @click="handleEnroll">수강 신청하기</button>
            <button 
              class="btn-wishlist" 
              :class="{ active: course.is_wished }" 
              @click="handleWishlistToggle"
            >
              {{ course.is_wished ? '♥' : '♡' }} 관심 강좌
            </button>
          </div>
        </div>
        <div class="hero-image">
          <img :src="course.course_image" :alt="course.name">
        </div>
      </div>
    </section>

    <div class="container layout-container">
      <main class="course-main">
        <nav class="content-nav">
          <a href="#intro" :class="{ active: activeTab === 'intro' }" @click="activeTab = 'intro'">강좌 소개</a>
          <a href="#reviews" :class="{ active: activeTab === 'reviews' }" @click="activeTab = 'reviews'">수강평</a>
        </nav>

        <section v-if="activeTab === 'intro'" id="intro" class="detail-section">
          <h2>강좌 소개</h2>
          <div class="summary-box" v-html="formattedSummary"></div>
        </section>

        <section v-if="activeTab === 'reviews'" id="reviews" class="detail-section">
          <CourseReviewSection :course-id="route.params.id" />
        </section>
      </main>

      <aside class="course-sidebar">
        <div class="info-card">
          <h3>수강 정보</h3>
          <ul class="info-list">
            <li><span>운영 기관</span> <strong>{{ course.org_name }}</strong></li>
            <li><span>교수진</span> <strong>{{ course.professor }}</strong></li>
            <li><span>분류</span> <strong>{{ course.classfy_name }} &gt; {{ course.middle_classfy_name }}</strong></li>
            <li class="divider"></li>
            <li><span>수강 기간</span> <strong>{{ course.study_start }} ~ {{ course.study_end }}</strong></li>
            <li><span>신청 기간</span> <strong>{{ course.enrollment_start }} ~ {{ course.enrollment_end }}</strong></li>
            <li class="divider"></li>
            <li><span>총 주차</span> <strong>{{ course.week }}주 과정</strong></li>
            <li><span>총 학습 시간</span> <strong>{{ Math.round(course.course_playtime / 3600) }}시간</strong></li>
            <li><span>이수증</span> <strong>{{ course.certificate_yn === 'Y' ? '발급 가능' : '해당 없음' }}</strong></li>
          </ul>
          <a :href="course.url" target="_blank" class="btn-external">K-MOOC 원문 보기 ↗</a>
        </div>
      </aside>
    </div>

    <section class="recommend-section container">
      <div class="section-title">
        <h2>이 강좌와 유사한 추천 강좌 ✨</h2>
        <p>AI가 분석한 학습 맥락이 비슷한 강좌들입니다.</p>
      </div>
      <div class="course-grid">
        <CourseCard
          v-for="rec in recommendedCourses"
          :key="rec.id"
          v-bind="rec"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/api/index';
import { getCourseDetail, getRecommendedCourses } from '@/api/courses';
import { addWishlist, removeWishlist } from '@/api/mypage';
import CourseCard from '@/components/common/CourseCard.vue';
import CourseReviewSection from '@/components/course/CourseReviewSection.vue';

const route = useRoute();
const router = useRouter();
const activeTab = ref('intro');
const course = ref(null);
const recommendedCourses = ref([]);

const formattedSummary = computed(() => {
  return course.value?.summary ? course.value.summary.replace(/\n/g, '<br>') : '';
});

// 데이터 로드 통합 함수
const fetchData = async () => {
  const courseId = route.params.id;
  try {
    // 1. 강좌 상세
    const detailRes = await getCourseDetail(courseId);
    course.value = detailRes.data;

    // 2. AI 추천 강좌
    const recommendRes = await getRecommendedCourses(courseId);
    recommendedCourses.value = recommendRes.data;
  } catch (error) {
    console.error("데이터 로드 실패:", error);
  }
};

// 찜하기 토글
const handleWishlistToggle = async () => {
  if (!course.value) return;
  
  const courseId = course.value.id;
  try {
    if (course.value.is_wished) {
      await removeWishlist(courseId);
      course.value.is_wished = false;
    } else {
      await addWishlist(courseId);
      course.value.is_wished = true;
    }
  } catch (error) {
    if (error.response?.status === 401) {
      if (confirm('로그인이 필요한 기능입니다. 로그인 페이지로 이동할까요?')) {
        router.push({ name: 'Login', query: { redirect: route.fullPath } });
      }
    } else {
      alert('요청 처리 중 오류가 발생했습니다.');
    }
  }
};

const handleEnroll = () => {
  if (course.value?.url) window.open(course.value.url, '_blank');
};

onMounted(fetchData);
</script>

<style scoped>
/* 기본 레이아웃 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.layout-container {
  display: grid;
  grid-template-columns: 1fr 350px; /* 메인 콘텐츠와 사이드바 비율 */
  gap: 40px;
  margin-top: 40px;
  margin-bottom: 80px;
}

/* 히어로 섹션 (상단 배경) */
.course-hero {
  background-color: #f9fafb;
  padding: 60px 0;
  border-bottom: 1px solid #e5e7eb;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
}

.hero-text { flex: 1; }

.university-tag {
  color: #6366f1;
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 12px;
}

.course-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #111827;
  line-height: 1.2;
  margin-bottom: 20px;
}

.instructor-info {
  font-size: 1.1rem;
  color: #4b5563;
  margin-bottom: 24px;
}

.course-stats-inline {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  align-items: center;
}

.rating-badge {
  background: #fef3c7;
  color: #d97706;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 700;
}

.hero-image img {
  width: 480px;
  height: 270px;
  object-fit: cover;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

/* 버튼 스타일 */
.action-buttons { display: flex; gap: 12px; }

.btn-enroll {
  background: #2563eb;
  color: white;
  padding: 14px 28px;
  border-radius: 8px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-wishlist {
  background: white;
  border: 1px solid #d1d5db;
  padding: 14px 24px;
  border-radius: 8px;
  cursor: pointer;
}

.btn-wishlist.active {
  color: #ef4444;
  border-color: #ef4444;
  background: #fef2f2;
}

/* 탭 메뉴 */
.content-nav {
  display: flex;
  gap: 30px;
  border-bottom: 2px solid #f3f4f6;
  margin-bottom: 30px;
}

.content-nav a {
  padding: 15px 5px;
  text-decoration: none;
  color: #6b7280;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.content-nav a.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

/* 사이드바 정보 카드 */
.info-card {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 30px;
  border-radius: 16px;
  position: sticky;
  top: 20px;
}

.info-list { list-style: none; padding: 0; }
.info-list li {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 0.95rem;
}

.info-list li span { color: #6b7280; }

.btn-external {
  display: block;
  text-align: center;
  margin-top: 20px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 8px;
  text-decoration: none;
  color: #374151;
  font-weight: 600;
}

/* 추천 섹션 */
.recommend-section { padding: 60px 0; border-top: 1px solid #e5e7eb; }
.course-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-top: 30px;
}

.divider { height: 1px; background: #e5e7eb; margin: 15px 0; list-style: none; }
.summary-box { line-height: 1.8; color: #374151; }
</style>