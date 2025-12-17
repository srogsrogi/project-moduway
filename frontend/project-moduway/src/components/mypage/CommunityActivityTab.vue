<template>
  <div class="tab-content active">
    <h3>커뮤니티 활동 요약</h3> 
    
    <div class="status-grid community-summary" style="border-bottom: 1px solid var(--section-separator); padding-bottom: 30px;">
        <div class="status-item">
            <a href="#"><strong>12건</strong><span>내가 작성한 글</span></a>
        </div>
        <div class="status-item">
            <a href="#"><strong>25건</strong><span>내가 작성한 댓글</span></a>
        </div>
        <div class="status-item">
            <a href="#"><strong>7건</strong><span>스크랩한 글</span></a>
        </div>
        <div class="status-item">
            <a href="#"><strong>48개</strong><span>받은 좋아요</span></a>
        </div>
    </div>
    
    <div class="community-list-section">
        <div class="search-header">
            <h4>📝 내가 작성한 글</h4>
        </div>
        <ul>
            <li><a href="#"><span class="post-category">[자유]</span><span class="post-title">이번에 들은 강의 후기 남깁니다. 정말 좋았어요 추천합니다.</span><span class="post-info">12.15</span></a></li>
            <li><a href="#"><span class="post-category">[Q&A]</span><span class="post-title">React 훅 사용 시 주의할 점이 뭘까요?</span><span class="post-info">12.10</span></a></li>
            <li><a href="#"><span class="post-category">[스터디]</span><span class="post-title">주말 알고리즘 스터디원 모집</span><span class="post-info">12.01</span></a></li>
            <li><a href="#"><span class="post-category">[정보]</span><span class="post-title">파이썬 라이브러리 추천 및 활용법</span><span class="post-info">11.28</span></a></li>
            <li><a href="#"><span class="post-category">[자유]</span><span class="post-title">개발 공부 시작하시는 분들께 드리는 팁</span><span class="post-info">11.15</span></a></li>
        </ul>
        <div class="footer-link-box"><a href="#">전체 보기 ></a></div>
    </div>
    
    <div class="community-list-section">
        <div class="search-header">
            <h4>💬 내가 작성한 댓글</h4>
        </div>
        <ul>
            <li><a href="#"><span class="post-category">[Re: Q&A]</span><span class="post-title">저도 그 부분에서 좀 헷갈렸는데, XXX 자료가 도움이 됐어요.</span><span class="post-info">12.16</span></a></li>
            <li><a href="#"><span class="post-category">[Re: 자유]</span><span class="post-title">강의 후기 잘 봤습니다! 덕분에 수강 결정했어요.</span><span class="post-info">12.15</span></a></li>
            <li><a href="#"><span class="post-category">[Re: 스터디]</span><span class="post-title">스터디 참여하고 싶은데, 자세한 내용은 쪽지로 보내주실 수 있나요?</span><span class="post-info">12.10</span></a></li>
            <li><a href="#"><span class="post-category">[Re: 정보]</span><span class="post-title">아, 파이썬에서 그 라이브러리 사용하면 정말 편하죠.</span><span class="post-info">12.05</span></a></li>
            <li><a href="#"><span class="post-category">[Re: Q&A]</span><span class="post-title">비동기 문제는 콜백 함수 대신 Promise나 Async/Await을 써보세요.</span><span class="post-info">11.30</span></a></li>
        </ul>
        <div class="footer-link-box"><a href="#">전체 보기 ></a></div>
    </div>
    
    <div class="community-list-section">
        <div class="search-header">
            <h4>🔖 스크랩한 글</h4>
        </div>
        <ul>
            <li><a href="#"><span class="post-category">[정보]</span><span class="post-title">2026년 IT 트렌드 요약</span><span class="post-info">11.20</span></a></li>
            <li><a href="#"><span class="post-category">[자유]</span><span class="post-title">취업 포트폴리오 팁 공유</span><span class="post-info">11.05</span></a></li>
            <li><a href="#"><span class="post-category">[Q&A]</span><span class="post-title">HTTP 상태코드 헷갈릴 때 보는 정리</span><span class="post-info">10.28</span></a></li>
            <li><a href="#"><span class="post-category">[스터디]</span><span class="post-title">자바 백엔드 프로젝트 함께 하실 분 구해요.</span><span class="post-info">10.15</span></a></li>
            <li><a href="#"><span class="post-category">[정보]</span><span class="post-title">개발자 필수 면접 질문 50선</span><span class="post-info">10.01</span></a></li>
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

/* Status Grid */
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; text-align: center; }
.status-item { border: 1px solid var(--border); border-radius: 6px; transition: 0.2s; cursor: pointer; background: #fff; overflow: hidden; }
.status-item:hover { border-color: var(--primary); background-color: var(--primary-light); }
.status-item a { display: block; padding: 15px; width: 100%; height: 100%; text-decoration: none; color: inherit; }
.status-item strong { display: block; font-size: 32px; font-weight: 800; color: var(--primary); margin-bottom: 5px; line-height: 1.2; }
.status-item span { font-size: 14px; color: var(--text-sub); display: block; }
.community-summary strong { font-size: 24px !important; }

/* 커뮤니티 목록 스타일 */
.community-list-section { margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid var(--section-separator); }
.community-list-section:last-child { margin-bottom: 0; border-bottom: none; }

.community-list-section .search-header { margin-bottom: 15px; } 
.community-list-section h4 { font-size: 18px; font-weight: 700; color: var(--text-main); margin: 0; }

.community-list-section ul { border-top: 1px solid var(--border-dark); padding: 0; margin: 0; }
.community-list-section li { border-bottom: 1px dashed var(--border); list-style: none; }
.community-list-section li a { display: flex; justify-content: space-between; align-items: center; padding: 12px 5px; font-size: 15px; color: var(--text-main); transition: color 0.2s; width: 100%; }
.community-list-section li a:hover { color: var(--primary-dark); background-color: #fafafa; }
.community-list-section .post-category { font-size: 13px; color: var(--primary); font-weight: 600; flex-shrink: 0; width: 80px; }
.community-list-section .post-title { flex-grow: 1; margin-right: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; text-align: left; }
.community-list-section .post-info { font-size: 13px; color: var(--text-sub); flex-shrink: 0; width: 80px; text-align: right; }

.footer-link-box { text-align: right; margin-top: 12px; }
.footer-link-box a { font-size: 13px; color: var(--text-sub); padding: 5px; border-bottom: 1px solid transparent; transition: 0.2s; }
.footer-link-box a:hover { color: var(--primary); border-bottom-color: var(--primary); }

@media (max-width: 768px) {
    .status-grid { grid-template-columns: repeat(2, 1fr); }
    .community-list-section .search-header { margin-bottom: 10px; }
    .community-list-section .post-category { width: 60px; }
    .community-list-section .post-info { display: none; }
}
</style>