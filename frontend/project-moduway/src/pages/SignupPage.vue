<template>
  <div class="signup-page-wrapper">
    <div class="signup-container">
      <div class="signup-card">
        <header class="signup-header">
          <h1 class="signup-title">회원가입</h1>
          <p class="signup-desc">Life-Learn의 다양한 강좌를 만나보세요.</p>
        </header>

        <form @submit.prevent="handleSignup">
          
          <div class="form-group">
            <label for="username" class="form-label">아이디 <span class="required-mark">*</span></label>
            <div class="input-with-btn">
              <input 
                type="text" 
                id="username" 
                class="form-input" 
                placeholder="6자 이상 영문/숫자 조합" 
                v-model="form.username" 
                required
              >
              <button type="button" class="btn-outline">중복확인</button>
            </div>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">비밀번호 <span class="required-mark">*</span></label>
            <input 
              type="password" 
              id="password" 
              class="form-input" 
              placeholder="8자 이상 영문/숫자/특수문자 포함" 
              v-model="form.password" 
              required
            >
          </div>

          <div class="form-group">
            <label for="password-confirm" class="form-label">비밀번호 확인 <span class="required-mark">*</span></label>
            <input 
              type="password" 
              id="password-confirm" 
              class="form-input" 
              placeholder="비밀번호를 한번 더 입력해주세요" 
              v-model="form.passwordConfirm" 
              required
            >
            <p class="helper-text" :class="passwordMatchClass">{{ passwordMatchMsg }}</p>
          </div>

          <div class="form-group">
            <label for="name" class="form-label">이름 <span class="required-mark">*</span></label>
            <input 
              type="text" 
              id="name" 
              class="form-input" 
              placeholder="김싸피" 
              v-model="form.name" 
              required
            >
          </div>

          <div class="form-group">
            <label for="email" class="form-label">이메일 <span class="required-mark">*</span></label>
            <div class="input-with-btn">
              <input 
                type="email" 
                id="email" 
                class="form-input" 
                placeholder="example@email.com" 
                v-model="form.email" 
                required
              >
              <button type="button" class="btn-outline">인증요청</button>
            </div>
          </div>

          <div class="terms-box">
            <label class="checkbox-group check-all">
              <input type="checkbox" v-model="allTermsChecked" @change="toggleAllTerms">
              <span>이용약관 전체 동의</span>
            </label>
            
            <label class="checkbox-group">
              <input type="checkbox" class="term-item" v-model="form.terms.service" required>
              <span>(필수) 서비스 이용약관 동의</span>
              <a href="#" class="terms-link">보기</a>
            </label>
            
            <label class="checkbox-group">
              <input type="checkbox" class="term-item" v-model="form.terms.privacy" required>
              <span>(필수) 개인정보 수집 및 이용 동의</span>
              <a href="#" class="terms-link">보기</a>
            </label>
            
            <label class="checkbox-group">
              <input type="checkbox" class="term-item" v-model="form.terms.marketing">
              <span>(선택) 마케팅 정보 수신 동의</span>
            </label>
          </div>

          <button type="submit" class="btn-submit">가입하기</button>

          <div class="login-link-area">
            이미 계정이 있으신가요? <router-link to="/login" class="login-link">로그인</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const form = ref({
  username: '',
  password: '',
  passwordConfirm: '',
  name: '',
  email: '',
  terms: {
    service: false,
    privacy: false,
    marketing: false,
  }
});

// Password Matching Logic
const passwordMatchMsg = computed(() => {
  if (!form.value.passwordConfirm) return '';
  return form.value.password === form.value.passwordConfirm 
    ? '비밀번호가 일치합니다.' 
    : '비밀번호가 일치하지 않습니다.';
});

const passwordMatchClass = computed(() => {
  if (!form.value.passwordConfirm) return '';
  return form.value.password === form.value.passwordConfirm 
    ? 'text-success' 
    : 'text-error';
});

// Terms Check Logic
const allTermsChecked = ref(false);

const toggleAllTerms = () => {
  const newState = allTermsChecked.value;
  form.value.terms.service = newState;
  form.value.terms.privacy = newState;
  form.value.terms.marketing = newState;
};

// Watch individual terms to update 'allTermsChecked' state
watch(() => form.value.terms, (newTerms) => {
  allTermsChecked.value = newTerms.service && newTerms.privacy && newTerms.marketing;
}, { deep: true });

const handleSignup = () => {
  if (!form.value.terms.service || !form.value.terms.privacy) {
    alert('필수 약관에 동의해주세요.');
    return;
  }
  // TODO: Implement actual signup API call
  console.log('Signup form submitted:', form.value);
  alert('회원가입 요청 (실제 API 연동 필요)');
};
</script>

<style scoped>
/* 1. 공통 테마 설정 (로그인 페이지와 통일) */
:root {
    --primary-color: #e11d48;
    --primary-hover: #be123c;
    --bg-color: #f3f4f6;
    --white: #ffffff;
    --text-dark: #111827;
    --text-gray: #6b7280;
    --border-color: #e5e7eb;
    --error-color: #ef4444;
    --success-color: #10b981;
}

.signup-page-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f3f4f6; /* var(--bg-color) */
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 80px);
    color: #111827; /* var(--text-dark) */
    padding: 40px 0;
    margin: 0;
}

/* 2. 회원가입 카드 컨테이너 (로그인보다 조금 더 넓게) */
.signup-container {
    width: 100%;
    max-width: 500px;
    padding: 20px;
}

.signup-card {
    background-color: #ffffff; /* var(--white) */
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
    border: 1px solid #e5e7eb; /* var(--border-color) */
}

/* 3. 헤더 */
.signup-header {
    text-align: center;
    margin-bottom: 30px;
}
.signup-title {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0 0 10px 0;
}
.signup-desc {
    color: #6b7280; /* var(--text-gray) */
    font-size: 0.95rem;
}

/* 4. 입력 폼 스타일 */
.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #111827; /* var(--text-dark) */
}
.required-mark { color: #e11d48; /* var(--primary-color) */ margin-left: 2px; }

/* 인풋 + 버튼 (중복확인용) 배치를 위한 Flex */
.input-with-btn {
    display: flex;
    gap: 10px;
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    font-size: 1rem;
    border: 1px solid #e5e7eb; /* var(--border-color) */
    border-radius: 8px;
    box-sizing: border-box;
    transition: all 0.2s;
}

.form-input:focus {
    outline: none;
    border-color: #e11d48; /* var(--primary-color) */
    box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.1);
}

/* 중복확인 등 소형 버튼 */
.btn-outline {
    white-space: nowrap;
    padding: 0 16px;
    background-color: #ffffff; /* var(--white) */
    border: 1px solid #e5e7eb; /* var(--border-color) */
    color: #111827; /* var(--text-dark) */
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-outline:hover {
    border-color: #e11d48; /* var(--primary-color) */
    color: #e11d48; /* var(--primary-color) */
    background-color: #fff1f2;
}

/* 헬퍼 텍스트 (유효성 검사 등) */
.helper-text {
    font-size: 0.85rem;
    margin-top: 6px;
    color: #6b7280; /* var(--text-gray) */
}
.text-error { color: #ef4444; /* var(--error-color) */ }
.text-success { color: #10b981; /* var(--success-color) */ }

/* 5. 약관 동의 박스 */
.terms-box {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb; /* var(--border-color) */
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 30px;
}

.checkbox-group {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-size: 0.95rem;
    cursor: pointer;
}
.checkbox-group:last-child { margin-bottom: 0; }

.checkbox-group input {
    width: 18px;
    height: 18px;
    margin-right: 10px;
    accent-color: #e11d48; /* var(--primary-color) */
    cursor: pointer;
}

.terms-link {
    font-size: 0.8rem;
    color: #6b7280; /* var(--text-gray) */
    text-decoration: underline;
    margin-left: auto; /* 우측 끝으로 밀기 */
}

/* 전체 동의 스타일 강조 */
.check-all {
    border-bottom: 1px solid #e5e7eb; /* var(--border-color) */
    padding-bottom: 12px;
    margin-bottom: 12px;
    font-weight: 700;
}

/* 6. 하단 버튼 */
.btn-submit {
    width: 100%;
    padding: 16px;
    background-color: #e11d48; /* var(--primary-color) */
    color: #ffffff; /* var(--white) */
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
    transition: background-color 0.2s;
    box-shadow: 0 4px 6px rgba(225, 29, 72, 0.2);
    margin-bottom: 15px;
}
.btn-submit:hover { background-color: #be123c; /* var(--primary-hover) */ }

.login-link-area {
    text-align: center;
    font-size: 0.95rem;
    color: #6b7280; /* var(--text-gray) */
}
.login-link {
    color: #e11d48; /* var(--primary-color) */
    font-weight: 700;
    text-decoration: none;
}
.login-link:hover { text-decoration: underline; }
</style>