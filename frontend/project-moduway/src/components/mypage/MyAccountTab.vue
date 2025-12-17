<template>
  <div class="tab-content active">
    <h3>내 계정</h3> 
    <div class="account-info tab-section-container" style="border-bottom: none;">
        <dl>
            <dt>이름</dt><dd>김싸피</dd>
            <dt>아이디</dt><dd>ssafy123</dd>
            <dt>이메일</dt><dd>ssafy@email.com</dd>
            <dt>가입일</dt><dd>2024.12.01</dd>
            <dt>마케팅 수신</dt><dd style="color:green; font-weight:600;">동의</dd>
        </dl>
        <div class="link-box-right">
            <a href="#" class="btn btn-outline">정보 수정</a>
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

/* 계정 정보 */
.account-info dl { display: grid; grid-template-columns: 120px 1fr; gap: 15px; padding-bottom: 20px; margin-bottom: 0; }
.account-info dt { font-weight: 600; color: var(--text-sub); }
.link-box-right { text-align: right; margin-top: 15px; }

@media (max-width: 768px) {
    .account-info dl { grid-template-columns: 1fr; gap: 5px; }
    .account-info dt { margin-top: 10px; }
}
</style>