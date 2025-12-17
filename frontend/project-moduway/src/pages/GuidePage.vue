<template>
  <div class="guide-page">
    <!-- 헤더 섹션 -->
    <section class="guide-header">
      <div class="container">
        <h1>LIFE-LEARN 이용 가이드</h1>
        <p>배움의 여정을 시작하는 여러분을 환영합니다.<br>LIFE-LEARN을 100% 활용하는 방법을 알려드릴게요.</p>
      </div>
    </section>

    <div class="container content-wrapper">
      <!-- 탭 네비게이션 -->
      <aside class="guide-nav">
        <ul>
          <li :class="{ active: activeSection === 'start' }" @click="scrollTo('start')">시작하기</li>
          <li :class="{ active: activeSection === 'courses' }" @click="scrollTo('courses')">강좌 수강</li>
          <li :class="{ active: activeSection === 'community' }" @click="scrollTo('community')">커뮤니티</li>
          <li :class="{ active: activeSection === 'faq' }" @click="scrollTo('faq')">자주 묻는 질문</li>
        </ul>
      </aside>

      <!-- 가이드 내용 -->
      <main class="guide-content">
        
        <!-- 시작하기 -->
        <section id="start" class="guide-section">
          <h2>🚀 시작하기</h2>
          <div class="step-card">
            <div class="step-num">01</div>
            <div class="step-desc">
              <h3>회원가입 및 프로필 설정</h3>
              <p>이메일 또는 소셜 계정으로 간편하게 가입하고, 마이페이지에서 프로필을 설정하여 맞춤형 서비스를 경험하세요.</p>
            </div>
          </div>
          <div class="step-card">
            <div class="step-num">02</div>
            <div class="step-desc">
              <h3>관심 분야 설정</h3>
              <p>최초 로그인 시 또는 마이페이지에서 관심 직무와 스킬을 설정하여 개인화된 강좌를 추천받으세요.</p>
            </div>
          </div>
        </section>

        <!-- 강좌 수강 -->
        <section id="courses" class="guide-section">
          <h2>📚 강좌 수강 방법</h2>
          <p class="section-desc">국내 유수 대학의 명품 강좌를 무료로 만나보세요.</p>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="icon">🔍</span>
              <h3>강좌 검색 및 탐색</h3>
              <p>키워드 검색, 카테고리 필터를 통해 원하는 강좌를 찾거나 추천 강좌를 탐색해보세요.</p>
            </div>
            <div class="feature-item">
              <span class="icon">📝</span>
              <h3>나의 학습 현황</h3>
              <p>마이페이지에서 수강 중인 강좌의 진도율, 완료된 강좌, 누적 학습 시간 등을 한눈에 확인하세요.</p>
            </div>
            <div class="feature-item">
              <span class="icon">🎓</span>
              <h3>이수증 발급</h3>
              <p>특정 강좌의 모든 과정을 완료하면 이수증을 발급받을 수 있습니다.</p>
            </div>
          </div>
        </section>

        <!-- 커뮤니티 -->
        <section id="community" class="guide-section">
          <h2>💬 커뮤니티 활용</h2>
          <p class="section-desc">다른 학습자들과 소통하고 정보를 공유하며 학습 효과를 높여보세요.</p>
          <div class="info-box">
            <ul>
              <li>**게시판:** 다양한 주제의 게시판에서 자유롭게 글을 쓰고 댓글을 달 수 있습니다.</li>
              <li>**활동 요약:** 마이페이지에서 나의 게시글, 댓글, 스크랩, 받은 좋아요 현황을 확인할 수 있습니다.</li>
              <li>**검색:** 특정 키워드로 게시글을 검색하여 필요한 정보를 빠르게 찾을 수 있습니다.</li>
            </ul>
          </div>
        </section>

        <!-- FAQ -->
        <section id="faq" class="guide-section">
          <h2>❓ 자주 묻는 질문</h2>
          <div class="faq-list">
            <div class="faq-item">
              <div class="question">Q. LIFE-LEARN은 어떤 서비스인가요?</div>
              <div class="answer">LIFE-LEARN은 국내 주요 대학 및 기관의 우수 강좌를 온라인으로 무료 제공하는 학습 플랫폼입니다.</div>
            </div>
            <div class="faq-item">
              <div class="question">Q. 강좌는 모두 무료인가요?</div>
              <div class="answer">네, 모든 강좌는 무료로 수강할 수 있습니다.</div>
            </div>
            <div class="faq-item">
              <div class="question">Q. 학습 진도는 어떻게 관리하나요?</div>
              <div class="answer">마이페이지에서 개인별 학습 진도율, 수강 기간 등을 편리하게 관리할 수 있습니다.</div>
            </div>
          </div>
        </section>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const activeSection = ref('start');

const scrollTo = (id) => {
  activeSection.value = id;
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};
</script>

<style scoped>
.guide-page { padding-bottom: 100px; }

/* 헤더 */
.guide-header { 
  background: var(--primary-light); 
  color: var(--primary-dark);
  padding: 80px 0; 
  text-align: center; 
  margin-bottom: 60px;
}
.guide-header h1 { font-size: 36px; font-weight: 800; margin-bottom: 20px; }
.guide-header p { font-size: 18px; color: var(--text-sub); line-height: 1.6; }

.content-wrapper { display: flex; gap: 50px; position: relative; }

/* 사이드 네비게이션 */
.guide-nav { width: 200px; flex-shrink: 0; position: sticky; top: 100px; height: fit-content; }
.guide-nav ul { border-left: 2px solid var(--border); }
.guide-nav li { 
  padding: 10px 20px; 
  color: var(--text-sub); 
  cursor: pointer; 
  transition: 0.2s; 
  font-weight: 500; 
  position: relative;
}
.guide-nav li:hover { color: var(--primary-dark); }
.guide-nav li.active { color: var(--primary-dark); font-weight: 700; }
.guide-nav li.active::before { 
  content: ''; 
  position: absolute; 
  left: -2px; 
  top: 0; 
  height: 100%; 
  width: 2px; 
  background: var(--primary-dark); 
}

/* 메인 콘텐츠 */
.guide-content { flex: 1; max-width: 800px; }
.guide-section { margin-bottom: 80px; scroll-margin-top: 100px; }
.guide-section h2 { font-size: 28px; font-weight: 800; color: var(--text-main); margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid var(--text-main); }
.section-desc { font-size: 16px; color: var(--text-sub); margin-bottom: 30px; }

/* 단계별 카드 */
.step-card { display: flex; gap: 20px; background: var(--bg-light); padding: 30px; border-radius: 12px; margin-bottom: 20px; border: 1px solid transparent; transition: 0.3s; }
.step-card:hover { border-color: var(--primary-dark); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
.step-num { font-size: 32px; font-weight: 900; color: var(--primary-dark); opacity: 0.3; line-height: 1; }
.step-desc h3 { font-size: 20px; font-weight: 700; margin-bottom: 10px; }
.step-desc p { color: var(--text-sub); }

/* 특징 그리드 */
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature-item { text-align: center; padding: 30px 20px; border: 1px solid var(--border); border-radius: 12px; transition: 0.3s; }
.feature-item:hover { transform: translateY(-5px); border-color: var(--primary-dark); }
.feature-item .icon { font-size: 40px; display: block; margin-bottom: 20px; }
.feature-item h3 { font-size: 18px; font-weight: 700; margin-bottom: 10px; }
.feature-item p { font-size: 14px; color: var(--text-sub); word-break: keep-all; }

/* 정보 박스 */
.info-box { background: #f0f7ff; padding: 30px; border-radius: 12px; color: #333; }
.info-box li { margin-bottom: 10px; list-style-type: disc; margin-left: 20px; }
.info-box li:last-child { margin-bottom: 0; }

/* FAQ 리스트 */
.faq-list { display: flex; flex-direction: column; gap: 15px; }
.faq-item { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.question { background: var(--bg-light); padding: 20px; font-weight: 700; cursor: default; }
.answer { padding: 20px; border-top: 1px solid var(--border); color: var(--text-sub); background: white; }

/* 반응형 */
@media (max-width: 768px) {
  .content-wrapper { flex-direction: column; }
  .guide-nav { display: none; }
  .feature-grid { grid-template-columns: 1fr; }
  .guide-header { padding: 60px 0; }
  .guide-header h1 { font-size: 28px; }
}
</style>