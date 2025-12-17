<template>
  <div class="tab-content active">
    <h3>관심 분야 설정</h3> 
    
    <div class="preference-setting tab-section-container">
        <div class="info-header">관심 직무</div>
        <div style="font-size:14px; color:var(--text-sub); margin-bottom:15px;">
            설정하신 직무를 기반으로 맞춤형 강의를 추천해 드립니다.
        </div>
        <div class="job-tags">
            <a href="#">IT·인터넷</a>
            <a href="#">경영·사무</a>
            <a href="#">디자인</a>
            <a href="#">마케팅</a>
        </div>
        <div class="link-box-right">
            <a href="#" class="btn btn-outline" style="max-width: 180px;">직무 수정</a>
        </div>
    </div>

    <div class="preference-setting tab-section-container" style="border-bottom: none;">
        <div class="info-header">세부 관심 스킬</div>
        <div style="font-size:14px; color:var(--text-sub); margin-bottom:15px;">
            내가 배우고 싶은 구체적인 기술이나 도구를 설정하세요.
        </div>
        <div class="skill-tags">
            <span class="skill-tag">Python</span>
            <span class="skill-tag">React</span>
            <span class="skill-tag">UX/UI</span>
            <span class="skill-tag">데이터분석</span>
            <span class="skill-tag">디지털마케팅</span>
            <span class="skill-tag">Figma</span>
        </div>
        <div class="link-box-right">
            <a href="#" class="btn btn-outline" style="max-width: 180px;">스킬 설정 수정</a>
        </div>
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

/* 관심 직무 & 세부 스킬 태그 */
.preference-setting .info-header { font-weight: 700; font-size: 18px; color: var(--text-main); margin-bottom: 15px; }
.preference-setting .job-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
.preference-setting .job-tags a { background-color: var(--primary-light); color: var(--primary-dark); padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 13px; border: 1px solid var(--primary-light); transition: 0.2s; display: inline-block; }
.preference-setting .job-tags a:hover { background-color: var(--primary); color: #fff; border-color: var(--primary); }

.skill-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.skill-tag { 
    padding: 6px 12px; 
    border: 1px solid var(--border-dark); 
    border-radius: 4px; 
    font-size: 13px; 
    color: var(--text-main); 
    background: #fff;
    display: inline-block;
    cursor: default;
}
.skill-tag::before { content: "#"; color: var(--primary); margin-right: 2px; font-weight: 700; }

.link-box-right { text-align: right; margin-top: 15px; }
</style>