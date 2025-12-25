<template>
  <div class="community-main container">
    <div class="layout-grid">
      
      <BoardCategoryList @select-board="handleBoardSelect" />

      <div class="board-content">
        
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
        
        <PostList :posts="posts" :total-count="totalCount" :loading="loading" />
        
        <!-- Pagination -->
        <div class="pagination" v-if="totalPages > 1">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1" 
            @click="changePage(currentPage - 1)"
          >
            &lt;
          </button>
          
          <button 
            v-for="page in visiblePages" 
            :key="page" 
            class="page-btn" 
            :class="{ current: currentPage === page }"
            @click="changePage(page)"
          >
            {{ page }}
          </button>
          
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages" 
            @click="changePage(currentPage + 1)"
          >
            &gt;
          </button>
        </div>

      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import BoardCategoryList from '@/components/community/BoardCategoryList.vue';
import PostList from '@/components/community/PostList.vue';
import { getPostsByBoardId, searchPosts } from '@/api/community';

const currentBoardTitle = ref('⭐ BEST 인기글');
const currentBoardId = ref(null);
const isAllSearch = ref(true);
const searchQuery = ref('');
const posts = ref([]);
const totalCount = ref(0);
const loading = ref(false);

// Pagination State
const currentPage = ref(1);
const itemsPerPage = 10; // 백엔드 기본 설정 (PAGE_SIZE)

const searchPlaceholder = computed(() => {
  return isAllSearch.value ? '전체 게시판에서 검색해보세요.' : `'${currentBoardTitle.value}' 게시판에서 검색해보세요.`;
});

const boardDescription = computed(() => {
  if (!currentBoardId.value) return '사용자들이 가장 많이 찾아 본 실시간 인기글을 모았습니다.';
  return `${currentBoardTitle.value} 게시판입니다. 자유롭게 소통해보세요.`;
});

// 전체 페이지 수 계산
const totalPages = computed(() => {
  return Math.ceil(totalCount.value / itemsPerPage);
});

// 화면에 보여줄 페이지 번호 계산 (최대 5개)
const visiblePages = computed(() => {
  const maxVisible = 5;
  const half = Math.floor(maxVisible / 2);
  let start = Math.max(1, currentPage.value - half);
  let end = Math.min(totalPages.value, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }
  
  const pages = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

// 게시글 목록 조회
const fetchPosts = async (boardId = null) => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value // 페이지 파라미터 추가
    };

    let response;
    if (boardId) {
      response = await getPostsByBoardId(boardId, params);
    } else {
      // BEST 인기글: 전체 게시글 조회 후 좋아요순 정렬 (검색 API 활용)
      // 검색 API도 q='' 이면 전체 목록 반환
      response = await searchPosts({ q: '', ...params });
    }
    
    // DRF Pagination 처리
    if (response.data.results) {
        posts.value = response.data.results;
        totalCount.value = response.data.count;
    } else {
        // Pagination이 적용되지 않은 응답인 경우 (예방 차원)
        posts.value = response.data;
        totalCount.value = response.data.length;
    }
  } catch (error) {
    console.error('게시글 목록 조회 실패:', error);
    alert('게시글을 불러오는데 실패했습니다.');
    posts.value = [];
  } finally {
    loading.value = false;
  }
};

// 페이지 변경 핸들러
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchPosts(currentBoardId.value);
  window.scrollTo(0, 0); // 상단으로 이동
};

// 게시판 선택
const handleBoardSelect = (payload) => {
  currentBoardTitle.value = payload.boardName;
  currentBoardId.value = payload.boardId === 'best_all' ? null : payload.boardId;
  isAllSearch.value = payload.isAllSearch;
  
  // 게시판 변경 시 페이지 초기화
  currentPage.value = 1;
  searchQuery.value = ''; // 검색어 초기화
  
  fetchPosts(currentBoardId.value);
};

// 검색
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    alert('검색어를 입력해주세요.');
    return;
  }

  // 검색 시 페이지 초기화
  currentPage.value = 1;
  loading.value = true;
  
  try {
    const params = { 
      q: searchQuery.value,
      page: currentPage.value 
    };
    
    if (!isAllSearch.value && currentBoardId.value) {
      params.board_id = currentBoardId.value;
    }
    
    const response = await searchPosts(params);
    
    // 검색 결과도 Pagination 응답 처리
    if (response.data.results) {
      posts.value = response.data.results;
      totalCount.value = response.data.count;
    } else {
      posts.value = response.data;
      totalCount.value = response.data.length;
    }
  } catch (error) {
    console.error('검색 실패:', error);
    alert('검색에 실패했습니다.');
  } finally {
    loading.value = false;
  }
};

// Helper function to extract main category from boardId
const getMainCategory = (boardId) => {
  if (!boardId || boardId === 'best_all') return '';
  return String(boardId).split('_')[0];
};

// Helper function to extract sub category from boardId
const getSubCategory = (boardId) => {
  if (!boardId || boardId === 'best_all') return '';
  const parts = String(boardId).split('_');
  return parts.length > 1 ? parts[1] : '';
};

// 초기 로드
onMounted(() => {
  fetchPosts();
});
</script>

<style scoped>
/* 커뮤니티 전용 레이아웃 */
.community-main { padding: 40px 0; width: 100%; }
.layout-grid {
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 30px;
    align-items: start;
}

/* 2. 메인 게시판 목록 */
.board-content {
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

.post-table .col-no { width: 8%; color: var(--text-sub); }
.post-table .col-type { width: 15%; font-weight: 600; color: var(--primary-dark); }
.post-table .col-title { text-align: left; padding-left: 15px; }
.post-table .col-title a { text-decoration: none; color: inherit; display: block; }
.post-table .col-author { width: 12%; }
.post-table .col-date { width: 12%; color: var(--text-sub); }
.post-table .col-likes { width: 8%; color: var(--primary); }

.post-table tr:hover {
    background-color: var(--primary-light);
}

/* 페이징 */
.pagination {
    display: flex;
    justify-content: center;
    margin-top: 30px;
    gap: 5px; /* 간격 추가 */
}
.page-btn { /* a 태그 대신 button 스타일로 변경 */
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-main);
    cursor: pointer;
    background: white;
    min-width: 32px;
}
.page-btn.current {
    background-color: var(--primary);
    color: white;
    border-color: var(--primary);
}
.page-btn:hover:not(.current):not(:disabled) {
    background-color: var(--bg-light);
}
.page-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* 반응형 */
@media (max-width: 992px) {
    .layout-grid {
        grid-template-columns: 1fr;
    }
}
</style>