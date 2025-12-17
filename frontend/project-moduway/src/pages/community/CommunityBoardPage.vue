<template>
  <div class="community-main container">
    <div class="layout-grid">
      
      <BoardCategoryList @select-board="handleBoardSelect" />

      <main class="main-content">
        
        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            class="search-input" 
            :placeholder="searchPlaceholder"
            @keyup.enter="handleSearch"
          >
          <button class="search-btn" @click="handleSearch">🔍</button>
        </div>
        <div class="board-header">
          <h1>{{ currentBoardTitle }}</h1>
          <router-link :to="{ path: '/community/write', query: { mainCat: getMainCategory(currentBoardId), subCat: getSubCategory(currentBoardId) } }" class="write-btn">글쓰기</router-link>
        </div>
        
        <div class="board-desc">
          {{ boardDescription }}
        </div>
        
        <table class="post-table">
          <thead>
            <tr>
              <th class="col-no">번호</th>
              <th class="col-type">게시판</th>
              <th class="col-title">제목</th>
              <th class="col-author">글쓴이</th>
              <th class="col-date">등록일</th>
              <th class="col-views">조회</th>
              <th class="col-likes">추천</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="post in posts" :key="post.id" :class="{ notice: post.isNotice }">
              <td class="col-no">{{ post.isNotice ? '공지' : post.id }}</td>
              <td class="col-type">{{ post.category }}</td>
              <td class="col-title">
                <router-link :to="`/community/posts/${post.id}`">{{ post.title }}</router-link>
              </td>
              <td class="col-author">{{ post.author }}</td>
              <td class="col-date">{{ post.date }}</td>
              <td class="col-views">{{ post.views }}</td>
              <td class="col-likes">{{ post.likes }}</td>
            </tr>
          </tbody>
        </table>
        
        <div class="pagination">
          <a href="#">&lt;&lt;</a>
          <a href="#">&lt;</a>
          <a href="#" class="current">1</a>
          <a href="#">2</a>
          <a href="#">3</a>
          <a href="#">4</a>
          <a href="#">5</a>
          <a href="#">&gt;</a>
          <a href="#">&gt;&gt;</a>
        </div>
      </main>
      
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import BoardCategoryList from '@/components/community/BoardCategoryList.vue';

const currentBoardTitle = ref('⭐ BEST 인기글');
const currentBoardId = ref('best_all');
const isAllSearch = ref(true);
const searchQuery = ref('');

const searchPlaceholder = computed(() => {
  return isAllSearch.value ? '전체 게시판에서 검색해보세요.' : `'${currentBoardTitle.value}' 게시판에서 검색해보세요.`;
});

const boardDescription = computed(() => {
  if (currentBoardId.value === 'best_all') return '랭커들이 가장 많이 찾아 본 실시간 인기글을 모았습니다.';
  if (currentBoardId.value === 'notice') return 'LIFE-LEARN의 새로운 소식과 알림을 확인하세요.';
  return `${currentBoardTitle.value} 게시판입니다. 자유롭게 소통해보세요.`;
});

// Helper function to extract main category from boardId
const getMainCategory = (boardId) => {
  if (boardId === 'best_all') return ''; // 'best_all'은 특정 카테고리가 아님
  if (boardId === 'notice') return 'notice';
  return boardId.split('_')[0];
};

// Helper function to extract sub category from boardId
const getSubCategory = (boardId) => {
  if (boardId === 'best_all' || boardId === 'notice') return '';
  return boardId.split('_')[1];
};

// Mock Data
const posts = ref([
  { id: 1001, isNotice: true, category: '공지/운영', title: '[필독] 커뮤니티 이용 수칙 및 운영 가이드 안내', author: '운영자', date: '2025.12.16', views: 50, likes: 0 },
  { id: 12, isNotice: false, category: '인공지능 소통방', title: '요즘 인공지능 윤리 강의 들으시는 분 계신가요?', author: 'AI마니아', date: '2025.12.15', views: 691, likes: 7 },
  { id: 11, isNotice: false, category: '수학 질문방', title: '수학의 정석: 이산수학 강의, 2주차 문제가 너무 어렵습니다 (도와주세요)', author: 'MATH_LVR', date: '2025.12.15', views: 520, likes: 5 },
  { id: 10, isNotice: false, category: '컴퓨터 강의후기', title: '[강의후기] 파이썬 기초 강의, 비전공자도 듣기 쉬웠어요!', author: '개발바라기', date: '2025.12.14', views: 759, likes: 12 },
  { id: 9, isNotice: false, category: '인문학 소통방', title: '서양 철학사 강의 들으면 인생이 바뀌나요? (진지)', author: '철학자K', date: '2025.12.14', views: 488, likes: 3 },
]);

const handleBoardSelect = (payload) => {
  currentBoardTitle.value = payload.boardName;
  currentBoardId.value = payload.boardId;
  isAllSearch.value = payload.isAllSearch;
  // TODO: Fetch posts for the selected board
  console.log(`Board selected: ${payload.boardId}`);
};

const handleSearch = () => {
  if (!searchQuery.value.trim()) {
    alert('검색어를 입력해주세요.');
    return;
  }
  
  let apiUrl = '';
  if (isAllSearch.value) {
    apiUrl = `community/posts/${searchQuery.value}`;
  } else {
    apiUrl = `community/board/${currentBoardId.value}/posts/${searchQuery.value}`;
  }
  
  console.log(`Search URL: ${apiUrl}`);
  alert(`"${searchQuery.value}"(으)로 검색 요청\nAPI Path: ${apiUrl}`);
};
</script>

<style scoped>
/* 커뮤니티 전용 레이아웃 */
.community-main { padding: 40px 0; }
.layout-grid {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 30px;
}

/* 2. 메인 게시판 목록 */
.main-content {
    background-color: var(--bg-white);
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}

/* 검색창 스타일 */
.search-container {
    position: relative;
    margin-bottom: 30px; 
    padding-bottom: 10px; 
    border-bottom: 1px solid var(--border); 
}
.search-input {
    width: 100%;
    padding: 12px 50px 12px 15px;
    border: 1px solid var(--primary); 
    border-radius: 8px;
    font-size: 16px;
    outline: none;
}
.search-btn {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--primary);
    cursor: pointer;
    font-size: 18px;
}

.board-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 15px;
    border-bottom: 2px solid var(--primary);
}

.board-header h1 {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    color: var(--primary-dark);
}

.board-header .write-btn {
    background-color: var(--primary);
    color: white; /* var(--white)가 정의되지 않았을 수 있으므로 직접 지정 */
    padding: 10px 20px;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 700;
    transition: background-color 0.2s;
}

.board-header .write-btn:hover {
    background-color: var(--primary-dark);
}

.board-desc {
    font-size: 0.95rem;
    color: var(--text-sub);
    padding: 20px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}

/* 게시판 목록 테이블 */
.post-table {
    width: 100%;
    border-collapse: collapse;
}

.post-table th, .post-table td {
    padding: 12px 10px;
    border-bottom: 1px solid var(--border);
    text-align: center;
    vertical-align: middle;
}

.post-table th {
    background-color: var(--bg-light);
    font-weight: 600;
    color: var(--text-main);
    font-size: 0.9rem;
}

.post-table td {
    font-size: 0.95rem;
    color: var(--text-main);
}

.post-table .col-no { width: 5%; color: var(--text-sub); }
.post-table .col-type { width: 15%; font-weight: 600; color: var(--primary-dark); }
.post-table .col-title { text-align: left; padding-left: 15px; }
.post-table .col-title a { text-decoration: none; color: inherit; display: block; }
.post-table .col-author { width: 10%; }
.post-table .col-date { width: 10%; color: var(--text-sub); }
.post-table .col-views { width: 5%; color: var(--text-sub); }
.post-table .col-likes { width: 5%; color: var(--primary); }

.post-table tr:hover {
    background-color: var(--primary-light);
}

/* 공지사항 스타일 */
.post-table tr.notice {
    background-color: var(--primary-light);
    font-weight: 700;
}
.post-table tr.notice .col-type { color: var(--primary-dark); }

/* 페이징 */
.pagination {
    display: flex;
    justify-content: center;
    margin-top: 30px;
}
.pagination a {
    padding: 8px 12px;
    margin: 0 4px;
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-main);
    cursor: pointer; /* cursor 추가 */
}
.pagination a.current {
    background-color: var(--primary);
    color: white;
    border-color: var(--primary);
}
.pagination a:hover:not(.current) { /* hover 효과 추가 */
    background-color: var(--bg-light);
}

/* 반응형 */
@media (max-width: 992px) {
    .layout-grid {
        grid-template-columns: 1fr;
    }
}
</style>