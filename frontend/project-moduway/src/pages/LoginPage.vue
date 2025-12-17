<template>
  <div class="login-page-wrapper">
    <div class="login-container">
      <div class="login-card">
        <router-link to="/" class="brand-logo">
          Life-<span>LEARN</span>
        </router-link>
        <p class="form-title">서비스 이용을 위해 로그인해주세요</p>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username" class="form-label">아이디</label>
            <input 
              type="text" 
              id="username" 
              class="form-input" 
              placeholder="example@email.com" 
              v-model="username" 
              required
            >
          </div>

          <div class="form-group">
            <label for="password" class="form-label">비밀번호</label>
            <input 
              :type="passwordFieldType" 
              id="password" 
              class="form-input" 
              placeholder="비밀번호를 입력하세요" 
              v-model="password" 
              required
            >
            <button type="button" class="toggle-pw" @click="togglePasswordVisibility">
              <span v-if="passwordFieldType === 'password'">👁️</span>
              <span v-else>🔒</span>
            </button>
          </div>

          <div class="form-options">
            <label class="checkbox-container">
              <input type="checkbox" v-model="rememberMe"> 로그인 상태 유지
            </label>
            <a href="#" class="find-pw-link">비밀번호 찾기</a>
          </div>

          <button type="submit" class="btn-login">로그인</button>
        </form>

        <div class="divider">
          <span>SNS 계정으로 간편 로그인</span>
        </div>
        <div class="social-buttons">
          <button type="button" class="btn-social btn-google">
            <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" width="18" height="18">
            Google 계정으로 로그인
          </button>
        </div>

        <div class="signup-area">
          아직 계정이 없으신가요?
          <router-link to="/signup" class="signup-link">회원가입</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const passwordFieldType = ref('password');

const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password';
};

const handleLogin = () => {
  console.log('Login attempted');
  alert('로그인 시도');
};
</script>

<style scoped>
/* html_temp/로그인.html 스타일 그대로 가져옴 */
:root {
    --primary-color: #e11d48;
    --primary-hover: #be123c;
    --bg-color: #f3f4f6;
    --white: #ffffff;
    --text-dark: #111827;
    --text-gray: #6b7280;
    --border-color: #e5e7eb;
}

.login-page-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f3f4f6; /* var(--bg-color) 직접 적용 */
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 80px);
    color: #111827; /* var(--text-dark) */
    padding: 0;
    margin: 0;
}

.login-container {
    width: 100%;
    max-width: 420px;
    padding: 20px;
}

.login-card {
    background-color: #ffffff; /* var(--white) */
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
    border: 1px solid #e5e7eb; /* var(--border-color) */
}

.brand-logo {
    display: block;
    text-align: center;
    margin-bottom: 30px;
    color: #e11d48; /* var(--primary-color) */
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: -1px;
    text-decoration: none;
}

.brand-logo span { color: #111827; /* var(--text-dark) */ }

.form-title {
    text-align: center;
    font-size: 1.1rem;
    color: #6b7280; /* var(--text-gray) */
    margin-bottom: 30px;
    margin-top: 0;
}

.form-group {
    margin-bottom: 20px;
    position: relative;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #111827; /* var(--text-dark) */
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    font-size: 1rem;
    border: 1px solid #e5e7eb; /* var(--border-color) */
    border-radius: 8px;
    box-sizing: border-box;
    transition: all 0.2s;
    background-color: white;
}

.form-input:focus {
    outline: none;
    border-color: #e11d48; /* var(--primary-color) */
    box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.1);
}

.toggle-pw {
    position: absolute;
    right: 15px;
    top: 38px;
    background: none;
    border: none;
    cursor: pointer;
    color: #6b7280; /* var(--text-gray) */
    font-size: 1.2rem;
    padding: 0;
}
.toggle-pw:hover { color: #111827; }

.form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    font-size: 0.9rem;
}

.checkbox-container {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #6b7280; /* var(--text-gray) */
}

.checkbox-container input {
    margin-right: 8px;
    accent-color: #e11d48; /* var(--primary-color) */
    width: 16px;
    height: 16px;
}

.find-pw-link {
    text-decoration: none;
    color: #6b7280; /* var(--text-gray) */
    transition: color 0.2s;
}
.find-pw-link:hover {
    color: #e11d48; /* var(--primary-color) */
    text-decoration: underline;
}

.btn-login {
    width: 100%;
    padding: 14px;
    background-color: #e11d48; /* var(--primary-color) */
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: background-color 0.2s;
    box-shadow: 0 4px 6px rgba(225, 29, 72, 0.2);
    display: block;
}

.btn-login:hover {
    background-color: #be123c; /* var(--primary-hover) */
}

.divider {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 30px 0 20px 0;
    color: #6b7280; /* var(--text-gray) */
    font-size: 0.85rem;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #e5e7eb; /* var(--border-color) */
}
.divider span { margin: 0 10px; }

.social-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.btn-social {
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #e5e7eb; /* var(--border-color) */
    background-color: white;
    font-size: 0.95rem;
    font-weight: 500;
    color: #111827; /* var(--text-dark) */
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: background-color 0.2s;
    width: 100%;
}

.btn-google:hover { background-color: #f8f9fa; border-color: #d2e3fc; }

.signup-area {
    text-align: center;
    margin-top: 30px;
    font-size: 0.95rem;
    color: #6b7280; /* var(--text-gray) */
}
.signup-link {
    color: #e11d48; /* var(--primary-color) */
    text-decoration: none;
    font-weight: 700;
    margin-left: 5px;
}
.signup-link:hover { text-decoration: underline; }
</style>