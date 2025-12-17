<template>
    <footer>
        <div class="container footer-content">
            <div class="footer-info">
                <h3>LIFE-LEARN</h3>
                <p style="font-size:13px; color:#888;">
                    (우) 01121 서울특별시 테헤란로 싸피로 777<br>
                    COPYRIGHT © LIFE-LEARN. ALL RIGHTS RESERVED.
                </p>
            </div>
            <div class="footer-links">
                <a href="#">이용약관</a>
                <a href="#">개인정보처리방침</a>
                <a href="#">고객센터</a>
            </div>
        </div>
    </footer>
</template>

<script setup>
</script>

<style scoped>
footer { background: #f9f9f9; padding: 60px 0; border-top: 1px solid #eee; margin-top: 80px; }
.footer-content { display: flex; justify-content: space-between; align-items: flex-end; }
.footer-info h3 { color: var(--primary-dark); margin-bottom: 15px; }
.footer-links { display: flex; gap: 20px; }
.footer-links a { color: var(--text-sub); font-size: 14px; }
</style>