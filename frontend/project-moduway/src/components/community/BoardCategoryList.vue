<template>
  <aside class="sidebar-left">
    <h4>LIFE-LEARN 커뮤니티</h4>
    <ul class="category-list">
      <li 
        :class="{ active: currentBoard === 'best_all' }" 
        @click="selectBoard('best_all', '⭐ BEST 인기글', true)"
      >
        <a href="#">BEST 인기글</a>
      </li>
      <li 
        :class="{ active: currentBoard === 'notice' }" 
        @click="selectBoard('notice', '📢 공지/운영', true)"
      >
        <a href="#">📢 공지/운영</a>
      </li>
    </ul>
    
    <div v-for="group in boardGroups" :key="group.title">
      <div class="group-title" @click="toggleGroup(group)">
        {{ group.title }}
        <span class="toggle-icon">{{ group.isOpen ? '▲' : '▼' }}</span>
      </div>
      <ul class="category-list" v-show="group.isOpen">
        <li 
          v-for="board in group.boards" 
          :key="board.id"
          :class="{ active: currentBoard === board.id }"
          @click="selectBoard(board.id, board.name)"
        >
          <a href="#">{{ board.name }}</a>
        </li>
      </ul>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['select-board']);
const currentBoard = ref('best_all');

const createBoardGroup = (title, prefix) => ({
  title,
  isOpen: false, // Initial state: collapsed
  boards: [
    { id: `${prefix}_talk`, name: `${title} 시시콜콜 (소통방)` },
    { id: `${prefix}_review`, name: `${title} 왁자지껄 (강의후기)` },
    { id: `${prefix}_qna`, name: `${title} 주고받고 (강의질문방)` },
  ]
});

const boardGroups = ref([
  createBoardGroup('인문', 'humanity'),
  createBoardGroup('사회', 'social'),
  createBoardGroup('교육', 'education'),
  createBoardGroup('공학', 'engineering'),
  createBoardGroup('자연', 'natural'),
  createBoardGroup('의약', 'medical'),
  createBoardGroup('예체능', 'arts_pe'),
  createBoardGroup('융·복합', 'convergence'),
]);

const selectBoard = (boardId, boardName, isAllSearch = false) => {
  currentBoard.value = boardId;
  emit('select-board', { boardId, boardName, isAllSearch });
};

const toggleGroup = (group) => {
  group.isOpen = !group.isOpen;
};
</script>

<style scoped>
/* 1. 좌측 카테고리 네비게이션 */
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
    color: var(--text-main);
    padding: 15px 20px;
    background-color: var(--primary-light);
    margin: 0;
    border-bottom: 1px solid var(--border);
}

.category-list {
    padding: 0;
    margin: 0;
}

.category-list li {
    border-bottom: 1px solid var(--border);
    cursor: pointer;
}
.category-list li:last-child {
     border-bottom: none;
}

.category-list li a {
    display: block;
    padding: 12px 20px;
    color: var(--text-main);
    text-decoration: none;
    transition: background-color 0.15s;
    font-size: 0.95rem;
    font-weight: 500;
    position: relative;
}

.category-list li:hover a {
    background-color: var(--bg-light);
    color: var(--primary-dark);
}

.category-list li.active a {
    background-color: var(--primary);
    color: var(--bg-white);
    font-weight: 700;
}
.category-list li.active a::before {
     content: '';
     position: absolute;
     left: 0;
     top: 0;
     bottom: 0;
     width: 4px;
     background-color: var(--primary-dark);
}

/* 대분류 그룹 타이틀 */
.group-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--primary);
    padding: 15px 20px;
    background-color: #fff;
    border-top: 1px solid var(--border);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background-color 0.2s;
}
.group-title:first-child { border-top: none; }
.group-title:hover { background-color: var(--bg-light); }

.toggle-icon {
    font-size: 0.8rem;
    color: var(--text-sub);
}

@media (max-width: 992px) {
    .sidebar-left {
        display: none; /* 모바일/태블릿에서는 카테고리 숨김 - 추후 모바일 메뉴 등으로 대체 필요 */
    }
}
</style>