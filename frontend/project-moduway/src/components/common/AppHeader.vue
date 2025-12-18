<template>
    <header>
        <div class="container nav-wrapper">
            <router-link to="/" class="logo">LIFE-LEARN</router-link>
            <nav class="gnb">
                <router-link to="/guide">이용방법</router-link>
                <router-link to="/courses">강좌찾기</router-link>
                <router-link to="/community">커뮤니티</router-link>
                <router-link to="/mypage" v-if="isAuthenticated">마이페이지</router-link>
            </nav>
            <div class="user-menu">
                <template v-if="!isAuthenticated">
                    <router-link to="/login" class="btn btn-outline">로그인</router-link>
                    <router-link to="/signup" class="btn btn-primary">회원가입</router-link>
                </template>
                <template v-else>
                    <button @click="handleLogout" class="btn btn-outline btn-logout">로그아웃</button>
                </template>
            </div>
        </div>
    </header>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

// 반응형 참조를 직접 변수로 할당 (템플릿에서 자동 언래핑됨)
const isAuthenticated = authStore.isAuthenticated;

const handleLogout = async () => {
    await authStore.logout();
    alert('로그아웃되었습니다.');
    router.push('/');
};
</script>

<style scoped>
header { border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(255,255,255,0.95); z-index: 1000; backdrop-filter: blur(5px); }
.nav-wrapper { display: flex; justify-content: space-between; align-items: center; height: 80px; }
.logo { font-size: 24px; font-weight: 800; color: var(--primary-dark); letter-spacing: -0.5px; }
.gnb { display: flex; gap: 30px; font-weight: 500; font-size: 16px; }
.gnb a:hover, .gnb .router-link-active { color: var(--primary); }
.user-menu { display: flex; gap: 10px; }

/* 버튼 스타일 (기존 main.css에 있을 수 있으나 헤더 전용으로 명시) */
.btn {
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.2s;
}

.btn-outline {
    border: 1px solid #e5e7eb;
    background-color: white;
    color: #111827;
}
.btn-outline:hover {
    background-color: #f3f4f6;
}

.btn-logout {
    color: #e11d48;
    border-color: #fecaca;
}
.btn-logout:hover {
    background-color: #fff1f2;
    border-color: #e11d48;
}

.btn-primary {
    background-color: #e11d48;
    color: white;
    border: 1px solid #e11d48;
}
.btn-primary:hover {
    background-color: #be123c;
    border-color: #be123c;
}
</style>