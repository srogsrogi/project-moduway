<template>
  <div class="post-detail-main">
    <router-link to="/community" class="link-back">← 목록으로 돌아가기</router-link>
    <div class="post-container">
      
      <div class="post-category-tag">{{ post.category }}</div>
      <h1 class="post-header-title">
        {{ post.title }}
      </h1>

      <div class="post-meta-info">
        <div class="author-info">
          <div class="profile-img"></div>
          <span class="nickname">{{ post.author }}</span>
          <span style="color: var(--text-sub);">{{ post.date }} 등록</span>
        </div>
        <div class="meta-stats">
          <span>조회 {{ post.views }}</span>
          <span>추천 {{ post.likes }}</span>
          <span>스크랩 {{ post.scraps }}</span>
        </div>
      </div>

      <div class="post-content">
        <p v-for="(paragraph, index) in post.content.split('\n')" :key="index">{{ paragraph }}</p>
        <p v-if="post.tags" style="margin-top: 25px; font-style: italic; color: #999;">
            {{ post.tags }}
        </p>
      </div>

      <div class="post-actions">
        <button class="action-button" :class="{ active: post.liked }" @click="toggleLike">
          👍 추천
          <span style="color: inherit; font-size: 16px;">{{ post.likes }}</span>
        </button>
        <button class="action-button" :class="{ active: post.scraped }" @click="toggleScrap">
          📎 스크랩
          <span style="color: inherit; font-size: 16px;">{{ post.scraps }}</span>
        </button>
        <button class="action-button">
          ... 신고
        </button>
      </div>

      <div class="comment-section">
        <div class="comment-count">
          댓글 <span style="color: var(--primary-dark);">{{ comments.length }}</span>개
        </div>

        <div class="comment-input-box">
          <textarea placeholder="댓글을 남겨보세요. 매너 있는 댓글 문화 부탁드립니다." v-model="newCommentContent"></textarea>
          <div class="comment-submit">
            <button class="btn btn-primary" style="padding: 8px 15px;" @click="addComment">등록</button>
          </div>
        </div>

        <ul class="comment-list">
          <li v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-meta">
              <div class="profile-img"></div>
              <span class="nickname">{{ comment.author }}</span>
              <span class="date">{{ comment.date }}</span>
            </div>
            <div class="comment-content">
              {{ comment.content }}
            </div>
          </li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const post = ref({
  id: route.params.id,
  category: '컴퓨터 왁자지껄 (강의후기)',
  title: '[강의후기] 파이썬 기초 강의, 비전공자도 듣기 쉬웠어요!',
  author: '개발바라기',
  date: '2025.12.14',
  views: 759,
  likes: 12,
  scraps: 1,
  content: `안녕하세요! 저는 비전공자인데, 이번에 처음으로 파이썬 기초 강의를 수강해봤습니다.
처음에는 코딩이라는 것 자체가 너무 어렵게 느껴졌는데, 교수님께서 예제를 생활 속 이야기로 풀어주셔서 이해하기가 정말 쉬웠습니다. 특히 실습 위주로 진행되어서 단순히 이론만 듣는 것보다 훨씬 재미있었고 기억에도 잘 남았습니다.
혹시 컴퓨터 분야에 관심은 있지만 겁부터 나서 시작 못 하신 분들이 있다면, 이 강의 강력 추천합니다!`,
  tags: '#파이썬 #비전공자 #강의후기 #컴퓨터기초 #강력추천',
  liked: false,
  scraped: false,
});

const comments = ref([
  { id: 1, author: '코딩꿈나무', date: '2025.12.14 15:30', content: '오! 저도 이 강의 고민하고 있었는데 후기 감사합니다! 바로 신청해야겠어요.' },
  { id: 2, author: '자바마스터', date: '2025.12.14 16:10', content: '맞아요, 교수님 정말 좋으시죠. 파이썬 다음으로 자바 강의도 꼭 들어보세요!' },
]);

const newCommentContent = ref('');

const toggleLike = () => {
  post.value.liked = !post.value.liked;
  post.value.likes += post.value.liked ? 1 : -1;
  // TODO: API call to update like status
};

const toggleScrap = () => {
  post.value.scraped = !post.value.scraped;
  post.value.scraps += post.value.scraped ? 1 : -1;
  // TODO: API call to update scrap status
};

const addComment = () => {
  if (newCommentContent.value.trim() === '') {
    alert('댓글 내용을 입력해주세요.');
    return;
  }
  const newComment = {
    id: comments.value.length + 1, // Simple ID generation
    author: '현재 사용자 (Mock)', // TODO: Replace with actual user
    date: new Date().toLocaleString(),
    content: newCommentContent.value,
  };
  comments.value.push(newComment);
  newCommentContent.value = '';
  // TODO: API call to add comment
};

onMounted(() => {
  // In a real application, you would fetch post and comments data based on route.params.id
  console.log('Fetching post details for ID:', route.params.id);
});
</script>

<style scoped>
/* ================================================= */
/* 게시글 상세 스타일 */
/* ================================================= */
.post-detail-main { padding: 40px 0; max-width: 900px; margin: 0 auto; padding-left: 20px; padding-right: 20px;} /* Add padding for responsiveness */

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
}

.post-category-tag {
    display: inline-block;
    background-color: var(--primary-light);
    color: var(--primary-dark);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 20px;
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