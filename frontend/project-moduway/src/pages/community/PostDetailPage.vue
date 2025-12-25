<template>
  <div class="post-detail-main">
    <router-link to="/community" class="link-back">← 목록으로 돌아가기</router-link>

    <div v-if="loading" style="text-align: center; padding: 60px;">
      <p>게시글을 불러오는 중...</p>
    </div>

    <div v-else-if="post" class="post-container">

      <div class="post-category-tag" v-if="post.board">{{ getBoardKoreanName(post.board.name) }}</div>
      <h1 class="post-header-title">
        {{ post.title }}
      </h1>

      <div class="post-meta-info">
        <div class="author-info">
          <div class="profile-img"></div>
          <span class="nickname">{{ post.author.name }}</span>
          <span style="color: var(--text-sub);">{{ formatDate(post.created_at) }} 등록</span>
        </div>
        <div class="meta-stats">
          <span>추천 {{ post.likes_count }}</span>
          <span>댓글 {{ post.comments_count }}</span>
        </div>
      </div>

      <div class="post-content">
        <p v-for="(paragraph, index) in post.content.split('\n')" :key="index">{{ paragraph }}</p>
      </div>

      <div class="post-actions">
        <button class="action-button" :class="{ active: post.is_liked }" @click="toggleLike">
          👍 추천
          <span style="color: inherit; font-size: 16px;">{{ post.likes_count }}</span>
        </button>
        <button class="action-button" :class="{ active: post.is_scrapped }" @click="toggleScrap">
          📎 스크랩
        </button>
      </div>

      <div class="comment-section">
        
        <!-- 댓글 작성 폼 -->
        <CommentForm 
          :replyTo="replyTo" 
          @submit="addComment" 
          @cancel="cancelReply" 
        />

        <!-- 댓글 목록 -->
        <CommentList 
          :comments="post.comments"
          :postId="post.id"
          :currentUser="currentUser"
          @delete="handleDeleteComment"
          @reply="startReply"
        />

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getPostDetail, toggleLike as toggleLikeAPI, toggleScrap as toggleScrapAPI, createComment, deleteComment } from '@/api/community';
import { useAuthStore } from '@/stores/auth';
import CommentList from '@/components/community/CommentList.vue';
import CommentForm from '@/components/community/CommentForm.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const post = ref(null);
const loading = ref(false);
const replyTo = ref(null); // 답글 대상 댓글

const isAuthenticated = computed(() => authStore.isAuthenticated);
const currentUser = computed(() => authStore.user);

// 게시판 이름 매핑
const categoryMap = {
  humanity: '인문', social: '사회', education: '교육',
  engineering: '공학', natural: '자연', medical: '의약',
  arts_pe: '예체능', convergence: '융·복합', etc: '기타',
  notice: '공지'
};

const typeMap = {
  talk: '소통방', review: '강의후기', qna: '질문방'
};

const getBoardKoreanName = (boardName) => {
  if (!boardName) return '';
  if (boardName === 'notice') return '공지사항';

  const parts = boardName.split('_');
  if (parts.length === 2) {
    const cat = categoryMap[parts[0]] || parts[0];
    const type = typeMap[parts[1]] || parts[1];
    return `${cat}-${type}`;
  }
  return boardName;
};

// 날짜 포맷팅
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}.${month}.${day} ${hours}:${minutes}`;
};

// 게시글 상세 조회
const fetchPost = async () => {
  loading.value = true;
  try {
    const response = await getPostDetail(route.params.id);
    post.value = response.data;
  } catch (error) {
    console.error('게시글 조회 실패:', error);
    alert('게시글을 불러오는데 실패했습니다.');
    router.push('/community');
  } finally {
    loading.value = false;
  }
};

// 좋아요 토글
const toggleLike = async () => {
  if (!isAuthenticated.value) {
    alert('로그인이 필요한 기능입니다.');
    return;
  }

  try {
    const response = await toggleLikeAPI(route.params.id);
    post.value.is_liked = response.data.is_liked;
    post.value.likes_count = response.data.likes_count;
  } catch (error) {
    console.error('좋아요 실패:', error);
    alert('좋아요 처리에 실패했습니다.');
  }
};

// 스크랩 토글
const toggleScrap = async () => {
  if (!isAuthenticated.value) {
    alert('로그인이 필요한 기능입니다.');
    return;
  }

  try {
    const response = await toggleScrapAPI(route.params.id);
    post.value.is_scrapped = response.data.is_scrapped;
  } catch (error) {
    console.error('스크랩 실패:', error);
    alert('스크랩 처리에 실패했습니다.');
  }
};

// 댓글 작성
const addComment = async (content) => {
  if (!isAuthenticated.value) {
    alert('로그인이 필요한 기능입니다.');
    return;
  }

  try {
    const data = {
      content: content,
    };
    if (replyTo.value) {
      data.parent = replyTo.value.id;
    }

    await createComment(route.params.id, data);
    
    // 성공 시 초기화 및 갱신
    replyTo.value = null;
    await fetchPost(); 
  } catch (error) {
    console.error('댓글 작성 실패:', error);
    alert('댓글 작성에 실패했습니다.');
  }
};

// 댓글 삭제
const handleDeleteComment = async (commentId) => {
  if (!confirm('댓글을 삭제하시겠습니까?')) {
    return;
  }

  try {
    await deleteComment(route.params.id, commentId);
    await fetchPost(); // 댓글 삭제 후 새로고침
  } catch (error) {
    console.error('댓글 삭제 실패:', error);
    alert('댓글 삭제에 실패했습니다.');
  }
};

// 답글 작성 시작
const startReply = (comment) => {
  replyTo.value = comment;
  // CommentForm에 포커스를 주거나 스크롤 이동하는 로직을 추가하면 좋음 (선택사항)
};

// 답글 취소
const cancelReply = () => {
  replyTo.value = null;
};

onMounted(() => {
  fetchPost();
});
</script>

<style scoped>
/* ================================================= */
/* 게시글 상세 스타일 */
/* ================================================= */
.post-detail-main { padding: 40px 0; max-width: 900px; margin: 0 auto; padding-left: 20px; padding-right: 20px; width: 100%; } /* Add padding for responsiveness */

.post-container {
    background-color: var(--bg-white);
    padding: 30px 40px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    border: 1px solid var(--border);
}

/* 1. 제목 및 카테고리 */
.post-header-title {
    font-size: 28px;
    font-weight: 800;
    line-height: 1.4;
    margin-bottom: 10px;
    margin-top: 0;
}

.post-category-tag {
    display: inline-block;
    background-color: var(--primary-light);
    color: var(--primary-dark);
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 15px;
    margin-left: -6px;
}

/* 2. 작성자 및 메타 정보 */
.post-meta-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 15px;
    margin-bottom: 30px;
}

.author-info {
    display: flex;
    align-items: center;
    font-size: 14px;
}

.author-info .profile-img {
    width: 32px;
    height: 32px;
    background-color: #ddd;
    border-radius: 50%;
    margin-right: 10px;
    flex-shrink: 0;
}
.author-info .nickname {
    font-weight: 700;
    margin-right: 20px;
    white-space: nowrap;
}

.meta-stats {
    flex-shrink: 0;
    white-space: nowrap;
}
.meta-stats span {
    color: var(--text-sub);
    margin-left: 15px;
}

/* 3. 본문 내용 */
.post-content {
    min-height: 300px;
    font-size: 16px;
    line-height: 1.8;
    color: var(--text-main);
    padding-bottom: 40px;
    border-bottom: 1px solid var(--border);
    word-break: break-word;
}
.post-content p {
    margin-bottom: 15px;
}

/* 4. 좋아요/액션 버튼 */
.post-actions {
    display: flex;
    justify-content: center;
    padding: 30px 0;
    border-bottom: 1px solid var(--border);
}

.action-button {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 10px 20px;
    border: 1px solid var(--border);
    border-radius: 20px;
    margin: 0 10px;
    font-weight: 600;
    color: var(--text-sub);
    transition: 0.2s;
    cursor: pointer;
    background-color: var(--bg-white);
}
.action-button:hover {
    border-color: var(--primary);
    color: var(--primary);
    background-color: var(--primary-light);
}
.action-button.active {
    border-color: var(--primary);
    background-color: var(--primary);
    color: var(--bg-white);
}

/* 5. 댓글 영역 */
.comment-section {
    padding-top: 30px;
}

.comment-count {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 20px;
}

.comment-input-box textarea {
    width: 100%;
    min-height: 80px;
    padding: 15px;
    border: 1px solid var(--border);
    border-radius: 6px;
    resize: vertical; /* Only vertical resize */
    outline: none;
    font-size: 14px;
    font-family: inherit; /* Inherit font from body */
}

.comment-submit {
    display: flex;
    justify-content: flex-end;
    margin-top: 10px;
    margin-bottom: 30px;
}
.comment-submit .btn {
    padding: 8px 15px; /* btn-sm */
}

/* 개별 댓글 스타일 */
.comment-list {
    border-top: 1px solid var(--border);
}
.comment-item {
    padding: 15px 0;
    border-bottom: 1px solid var(--border);
}
.comment-meta {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}
.comment-meta .profile-img {
    width: 24px;
    height: 24px;
    background-color: #ddd;
    border-radius: 50%;
    margin-right: 8px;
    flex-shrink: 0;
}
.comment-meta .nickname {
    font-weight: 700;
    font-size: 13px;
    margin-right: 15px;
}
.comment-meta .date {
    font-size: 12px;
    color: var(--text-sub);
}
.comment-content {
    font-size: 14px;
    padding-left: 32px;
    color: var(--text-main);
    margin-bottom: 8px;
}

.comment-actions {
    padding-left: 32px;
    display: flex;
    gap: 10px;
}

.comment-actions .action-btn {
    background: none;
    border: none;
    color: var(--text-sub);
    font-size: 12px;
    cursor: pointer;
    padding: 4px 8px;
    transition: color 0.2s;
}

.comment-actions .action-btn:hover {
    color: var(--primary);
}

.comment-actions .action-btn.delete:hover {
    color: #dc2626;
}

.reply-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--primary-light);
    border-radius: 4px;
    margin-bottom: 8px;
    font-size: 13px;
    color: var(--primary-dark);
}

.reply-info .cancel-btn {
    background: none;
    border: none;
    color: var(--primary-dark);
    font-size: 12px;
    cursor: pointer;
    text-decoration: underline;
}

/* 반응형 */
@media (max-width: 768px) {
    .post-container {
        padding: 20px;
    }
    .post-header-title {
        font-size: 22px;
    }
    .meta-stats span {
        /* display: none; */ /* Keep important info */
        margin-left: 10px;
        font-size: 12px;
    }
    .post-meta-info {
        flex-wrap: wrap;
        gap: 10px;
    }
    .author-info {
        flex-grow: 1;
        min-width: 0;
    }
    .meta-stats {
        flex-grow: 1;
        text-align: right;
        min-width: 0;
    }
    .meta-stats span:first-child {
        margin-left: 0;
    }
    .action-button {
        padding: 8px 15px;
        font-size: 13px;
    }
}
</style>