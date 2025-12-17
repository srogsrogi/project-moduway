    <template>
    <header>
        <div class="container nav-wrapper">
            <router-link to="/" class="logo">LIFE-LEARN</router-link>
            <nav class="gnb">
                <router-link to="/guide">이용방법</router-link>
                <router-link to="/courses">강좌찾기</router-link>
                <router-link to="/community">커뮤니티</router-link>
                <router-link to="/mypage">마이페이지</router-link>
            </nav>
            <div class="user-menu">
                <router-link to="/login" class="btn btn-outline">로그인</router-link>
                <router-link to="/signup" class="btn btn-primary">회원가입</router-link>
            </div>
        </div>
    </header>
</template>

<script setup>
</script>

<style scoped>
header { border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(255,255,255,0.95); z-index: 1000; backdrop-filter: blur(5px); }
.nav-wrapper { display: flex; justify-content: space-between; align-items: center; height: 80px; }
.logo { font-size: 24px; font-weight: 800; color: var(--primary-dark); letter-spacing: -0.5px; }
.gnb { display: flex; gap: 30px; font-weight: 500; font-size: 16px; }
.gnb a:hover, .gnb .router-link-active { color: var(--primary); }
.user-menu { display: flex; gap: 10px; }
</style>