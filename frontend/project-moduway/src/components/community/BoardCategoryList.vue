<template>
  <aside class="sidebar-left">
    <h4>LIFE-LEARN 커뮤니티</h4>
    <ul class="category-list">
      <!-- 1. BEST 인기글 -->
      <li
        :class="{ active: currentBoard === 'best_all' }"
        @click="selectBoard('best_all', '⭐ BEST 인기글', true)"
      >
        <a href="#">⭐ BEST 인기글</a>
      </li>

      <!-- 2. 공지사항 -->
      <li
        :class="{ active: currentBoard === 'notice' }"
        @click="selectBoard('notice', '공지사항')"
      >
        <a href="#">📢 공지사항</a>
      </li>
    </ul>

    <div class="group-title">분야별 게시판</div>

    <ul class="category-list accordion-list">
      <li v-for="cat in categories" :key="cat.id" class="accordion-item">
        <!-- 대분류 (클릭 시 토글) -->
        <div class="accordion-header" @click="toggleCategory(cat.id)">
          <span>{{ cat.label }}</span>
          <span class="toggle-icon">{{ isOpen(cat.id) ? '▲' : '▼' }}</span>
        </div>

        <!-- 소분류 (펼쳐졌을 때만 보임) -->
        <ul v-show="isOpen(cat.id)" class="sub-category-list">
          <li
            v-for="sub in subCategories"
            :key="`${cat.id}_${sub.id}`"
            :class="{ active: currentBoard === `${cat.id}_${sub.id}` }"
            @click="selectBoard(`${cat.id}_${sub.id}`, `${cat.label} - ${sub.label}`)"
          >
            <a href="#">- {{ sub.label }}</a>
          </li>
        </ul>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['select-board']);
const currentBoard = ref('best_all');
const openCategories = ref([]); // 열려있는 카테고리 ID 목록

// 대분류 데이터 (9개)
const categories = [
  { id: 'humanity', label: '인문' },
  { id: 'social', label: '사회' },
  { id: 'education', label: '교육' },
  { id: 'engineering', label: '공학' },
  { id: 'natural', label: '자연' },
  { id: 'medical', label: '의약' },
  { id: 'arts_pe', label: '예체능' },
  { id: 'convergence', label: '융·복합' },
  { id: 'etc', label: '기타' },
];

// 소분류 데이터 (3개 공통)
const subCategories = [
  { id: 'talk', label: '소통방' },
  { id: 'review', label: '강의후기' },
  { id: 'qna', label: '질문방' },
];

// 토글 로직
const toggleCategory = (catId) => {
  if (openCategories.value.includes(catId)) {
    openCategories.value = openCategories.value.filter(id => id !== catId);
  } else {
    openCategories.value.push(catId);
  }
};

const isOpen = (catId) => {
  return openCategories.value.includes(catId);
};

// 게시판 선택
const selectBoard = (boardId, boardName, isAllSearch = false) => {
  currentBoard.value = boardId;
  emit('select-board', { boardId, boardName, isAllSearch });
};
</script>

<style scoped>
.sidebar-left {
    background-color: var(--bg-white);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    height: fit-content;
    overflow: hidden;
}

.sidebar-left h4 {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--primary);
    padding: 15px 20px;
    background-color: var(--primary-light);
    margin: 0;
    border-bottom: 1px solid var(--border);
}

.group-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--primary);
    padding: 15px 20px;
    background-color: #fff;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
}

.category-list { padding: 0; margin: 0; }
.category-list li > a {
    display: block;
    padding: 12px 20px;
    color: var(--text-main);
    text-decoration: none;
    transition: background-color 0.15s;
    font-size: 0.95rem;
    font-weight: 500;
}
.category-list li > a:hover {
    background-color: var(--bg-light);
    color: var(--primary-dark);
}
.category-list li.active > a {
    background-color: var(--primary);
    color: var(--bg-white);
    font-weight: 700;
}

/* 아코디언 스타일 */
.accordion-item { border-bottom: 1px solid var(--border); }
.accordion-header {
    padding: 12px 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: var(--text-main);
    background-color: #fff;
    transition: background-color 0.2s;
}
.accordion-header:hover { background-color: var(--bg-light); }
.toggle-icon { font-size: 0.8rem; color: var(--text-sub); }

/* 소분류 스타일 */
.sub-category-list { background-color: var(--bg-light); }
.sub-category-list li > a {
    padding-left: 35px; /* 들여쓰기 */
    font-size: 0.9rem;
    color: var(--text-sub);
}
.sub-category-list li.active > a {
    background-color: var(--primary-light); /* 소분류 활성 시 약간 연한 색 */
    color: var(--primary-dark);
}
</style>
