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
            <span class="vod-time">📺 VOD {{ formattedPlaytime }}</span>
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

        <section v-show="activeTab === 'intro'" id="intro" class="detail-section">
          <h2>강좌 소개</h2>
          <div class="iframe-wrapper">
            <iframe
              ref="summaryIframe"
              :srcdoc="wrappedHtml"
              class="summary-iframe"
              @load="resizeIframe"
              scrolling="no"
              frameborder="0"
            ></iframe>
          </div>
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
            <li><span>총 학습 시간</span> <strong>{{ formattedPlaytime }}</strong></li>
            <li><span>이수증</span> <strong>{{ course.certificate_yn === 'Y' ? '발급 가능' : '해당 없음' }}</strong></li>
          </ul>
          <a :href="course.url" target="_blank" class="btn-external">K-MOOC 바로가기 ↗</a>
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
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getCourseDetail, getRecommendedCourses } from '@/api/courses';
import { addWishlist, removeWishlist } from '@/api/mypage';
import CourseCard from '@/components/common/CourseCard.vue';
import CourseReviewSection from '@/components/course/CourseReviewSection.vue';

const route = useRoute();
const router = useRouter();
const activeTab = ref('intro');
const course = ref(null);
const recommendedCourses = ref([]);
const summaryIframe = ref(null);

// [핵심] iframe에 주입할 HTML 구성 (스타일 격리)
const wrappedHtml = computed(() => {
  const content = course.value?.raw_summary || 
                  (course.value?.summary ? course.value.summary.replace(/\n/g, '<br>') : '강좌 소개가 없습니다.');
  
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { 
            margin: 0; 
            padding: 15px; 
            font-family: 'Pretendard', -apple-system, sans-serif; 
            line-height: 1.7; 
            color: #374151; 
            word-break: break-all;
            overflow: hidden; 
          }
          /* 외부 고정 너비 강제 무력화 */
          * { max-width: 100% !important; box-sizing: border-box !important; }
          img { height: auto !important; display: block; margin: 15px auto; border-radius: 8px; }
          table { width: 100% !important; border-collapse: collapse; margin: 20px 0; display: table; }
          td, th { border: 1px solid #e5e7eb; padding: 10px; text-align: left; }
          p { margin: 1em 0; }
          a { color: #2563eb; }
        </style>
      </head>
      <body>${content}</body>
    </html>
  `;
});

// [핵심] iframe 높이 자동 조절
const resizeIframe = () => {
  const iframe = summaryIframe.value;
  if (iframe && iframe.contentWindow) {
    // 렌더링 완료 후 높이 측정을 위해 약간의 지연(nextTick) 적용
    nextTick(() => {
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      const height = doc.body.scrollHeight;
      iframe.style.height = height + 'px';
    });
  }
};

// VOD 시간 포맷팅
const formattedPlaytime = computed(() => {
  const seconds = course.value?.course_playtime || 0;
  const totalMinutes = Math.round(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) return minutes > 0 ? `${hours}시간 ${minutes}분` : `${hours}시간`;
  return `${minutes}분`;
});

// 수강신청 버튼 (외부 링크 이동)
const handleEnroll = () => {
  if (course.value && course.value.url) {
    window.open(course.value.url, '_blank');
  } else {
    alert('수강신청 링크가 없습니다.');
  }
};

// 찜하기 토글
const handleWishlistToggle = async () => {
  if (!course.value) return;

  try {
    if (course.value.is_wished) {
      await removeWishlist(course.value.id);
      course.value.is_wished = false;
    } else {
      await addWishlist(course.value.id);
      course.value.is_wished = true;
    }
  } catch (error) {
    console.error('찜하기 실패:', error);
    // 401 Unauthorized 에러 처리 (로그인 필요)
    if (error.response && error.response.status === 401) {
      if (confirm('로그인이 필요한 기능입니다. 로그인 페이지로 이동할까요?')) {
        router.push(`/login?redirect=${route.fullPath}`);
      }
    } else {
      alert('찜하기 처리에 실패했습니다.');
    }
  }
};

const fetchData = async (courseId) => {
  if (!courseId) return;
  try {
    const detailRes = await getCourseDetail(courseId);
    course.value = detailRes.data;

    const recommendRes = await getRecommendedCourses(courseId);
    recommendedCourses.value = recommendRes.data;
    
    activeTab.value = 'intro';
    window.scrollTo(0, 0);
  } catch (error) {
    console.error("데이터 로드 실패:", error);
  }
};

watch(() => route.params.id, (newId) => fetchData(newId));

// 창 크기 조절 시 iframe 높이 재계산
onMounted(() => {
  fetchData(route.params.id);
  window.addEventListener('resize', resizeIframe);
});
</script>

<style scoped>
/* 컨테이너 및 기본 레이아웃 */
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.layout-container { display: grid; grid-template-columns: 1fr 350px; gap: 40px; margin: 40px auto 80px; }

/* [수정] iframe 스타일 */
.iframe-wrapper {
  width: 100%;
  overflow: hidden;
  background: white;
  border-radius: 12px;
}

.summary-iframe {
  width: 100%;
  min-height: 400px;
  border: none;
  display: block;
  transition: height 0.2s ease;
}

/* 히어로 섹션 */
.course-hero { background-color: #f9fafb; padding: 60px 0; border-bottom: 1px solid #e5e7eb; }
.hero-content { display: flex; justify-content: space-between; align-items: center; gap: 40px; }
.course-title { font-size: 2.5rem; font-weight: 800; color: #111827; margin-bottom: 20px; }
.rating-badge { background: #fef3c7; color: #d97706; padding: 4px 12px; border-radius: 20px; font-weight: 700; }
.hero-image img { width: 480px; height: 270px; object-fit: cover; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }

/* 액션 버튼 스타일 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 30px;
}

.btn-enroll { 
  background: #2563eb; 
  color: white; 
  padding: 14px 28px; 
  border-radius: 8px; 
  font-weight: 700; 
  border: none; 
  cursor: pointer; 
  font-size: 1rem;
  transition: background 0.2s;
}
.btn-enroll:hover { background: #1d4ed8; }

.btn-wishlist {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 14px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}
.btn-wishlist:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}
.btn-wishlist.active {
  border-color: #e11d48;
  color: #e11d48;
  background: #fff1f2;
}

/* 네비게이션 및 기타 */
.content-nav { display: flex; gap: 30px; border-bottom: 2px solid #f3f4f6; margin-bottom: 30px; }
.content-nav a { padding: 15px 5px; text-decoration: none; color: #6b7280; font-weight: 600; border-bottom: 2px solid transparent; cursor: pointer; }
.content-nav a.active { color: #2563eb; border-bottom-color: #2563eb; }
.info-card { background: white; border: 1px solid #e5e7eb; padding: 30px; border-radius: 16px; position: sticky; top: 20px; }
.info-list { list-style: none; padding: 0; }
.info-list li { display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 0.95rem; }
.divider { height: 1px; background: #e5e7eb; margin: 15px 0; list-style: none; }
.btn-external { display: block; width: 100%; text-align: center; padding: 12px; background: #f3f4f6; color: #4b5563; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }
.btn-external:hover { background: #e5e7eb; }
.course-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 30px; }

/* 반응형 */
@media (max-width: 1024px) {
  .hero-content { flex-direction: column-reverse; align-items: stretch; }
  .hero-image img { width: 100%; height: auto; }
  .layout-container { grid-template-columns: 1fr; }
}
</style>
