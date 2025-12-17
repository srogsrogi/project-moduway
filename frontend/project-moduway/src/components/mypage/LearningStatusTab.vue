<template>
  <div class="tab-content active">
    <h3>나의 학습 현황</h3>
    
    <div class="status-grid tab-section-container" style="border-bottom: none; margin-bottom: 20px;">
        <div class="status-item">
            <a href="#"><strong>3</strong><span>수강 중</span></a>
        </div>
        <div class="status-item">
            <a href="#"><strong>5</strong><span>완료된 강의</span></a>
        </div>
        <div class="status-item">
            <a href="#"><strong>2</strong><span>관심 강좌</span></a>
        </div>
        <div class="status-item">
            <a href="#">
                <strong>120</strong>
                <span>누적 학습 시간(h)</span>
            </a>
        </div>
    </div>

    <div class="tab-section-container">
        <h4 style="font-size:18px; font-weight:700; margin-bottom:15px; color:var(--text-main);">최근 학습 기록</h4>
        <div class="learning-detail-box">
            <p style="margin-bottom:10px;">최근 수강 강좌: <strong style="color:var(--primary-dark);">웹 개발 심화 과정</strong></p>
            <div class="progress-bar"><div class="progress-fill" style="width: 75%;"></div></div>
            <div class="progress-text">
                <span>나의 진도율: 75%</span>
                <span>이번 주 학습 시간: 12시간 30분</span>
            </div>
            <div class="link-box-right">
                <a href="#" class="btn btn-primary">📚 강의 이어 듣기</a>
            </div>
        </div>
    </div>

    <div class="tab-section-container">
        <h4 style="font-size:18px; font-weight:700; margin-bottom:10px; color:var(--text-main);">수강 중인 강의</h4>
        <ul class="learning-course-list">
            <li class="learning-course-item">
                <div class="course-info">
                    <div class="course-title">알고리즘 코딩테스트 입문</div>
                    <div class="course-date">수강기간: ~2025.12.31</div>
                </div>
                <div class="course-progress">
                    <span class="progress-percent">60%</span>
                    <div class="progress-bar"><div class="progress-fill" style="width: 60%;"></div></div>
                </div>
                <div class="course-action">
                    <a href="#" class="btn btn-primary btn-sm">이어듣기</a>
                </div>
            </li>
            <li class="learning-course-item">
                <div class="course-info">
                    <div class="course-title">Vue.js 3 완벽 가이드</div>
                    <div class="course-date">수강기간: ~2026.01.15</div>
                </div>
                <div class="course-progress">
                    <span class="progress-percent">25%</span>
                    <div class="progress-bar"><div class="progress-fill" style="width: 25%;"></div></div>
                </div>
                <div class="course-action">
                    <a href="#" class="btn btn-primary btn-sm">이어듣기</a>
                </div>
            </li>
        </ul>
        <div class="footer-link-box"><a href="#">전체 보기 ></a></div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.tab-content { display: block; background-color: var(--bg-white); padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
.tab-content h3 { font-size: 20px; font-weight: 700; color: var(--primary-dark); border-bottom: 2px solid var(--primary-light); padding-bottom: 10px; margin-bottom: 20px; }

/* 섹션 컨테이너 */
.tab-section-container { padding-bottom: 30px; border-bottom: 1px solid var(--section-separator); margin-bottom: 30px; }
.tab-content > .tab-section-container:last-of-type { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

/* Status Grid */
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; text-align: center; }
.status-item { border: 1px solid var(--border); border-radius: 6px; transition: 0.2s; cursor: pointer; background: #fff; overflow: hidden; }
.status-item:hover { border-color: var(--primary); background-color: var(--primary-light); }
.status-item a { display: block; padding: 15px; width: 100%; height: 100%; text-decoration: none; color: inherit; }
.status-item strong { display: block; font-size: 32px; font-weight: 800; color: var(--primary); margin-bottom: 5px; line-height: 1.2; }
.status-item span { font-size: 14px; color: var(--text-sub); display: block; }

/* 최근 학습 기록 */
.learning-detail-box { padding: 20px; border-radius: 6px; border: 1px solid var(--border); background-color: var(--bg-light); }
.progress-bar { height: 8px; background: #ddd; border-radius: 4px; overflow: hidden; margin: 10px 0; }
.progress-fill { height: 100%; background: var(--primary); }
.progress-text { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-sub); }

/* 수강 중인 강의 목록 */
.learning-course-list { list-style: none; padding: 0; margin-top: 15px; }
.learning-course-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px dashed var(--border); }
.learning-course-item:last-child { border-bottom: none; }
.course-info { flex-grow: 1; min-width: 0; margin-right: 20px; }
.course-title { font-weight: 700; font-size: 16px; margin-bottom: 4px; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.course-date { font-size: 13px; color: var(--text-sub); }
.course-progress { width: 150px; margin-right: 20px; flex-shrink: 0; }
.course-progress .progress-bar { height: 6px; margin: 5px 0; background-color: #eee; }
.course-progress .progress-percent { font-size: 12px; font-weight: 700; color: var(--primary); float: right; }
.course-action { flex-shrink: 0; }

.footer-link-box { text-align: right; margin-top: 12px; }
.footer-link-box a { font-size: 13px; color: var(--text-sub); padding: 5px; border-bottom: 1px solid transparent; transition: 0.2s; }
.footer-link-box a:hover { color: var(--primary); border-bottom-color: var(--primary); }
.link-box-right { text-align: right; margin-top: 15px; }

@media (max-width: 768px) {
    .status-grid { grid-template-columns: repeat(2, 1fr); }
    .learning-course-item { flex-direction: column; align-items: flex-start; gap: 10px; }
    .course-info, .course-progress { width: 100%; margin-right: 0; }
    .course-action { align-self: flex-end; width: 100%; text-align: right; }
    .course-action .btn { width: 100%; }
}
</style>