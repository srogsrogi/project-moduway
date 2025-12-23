<template>
  <div class="post-list-container">
    <div v-if="loading" class="loading-state">
      <p>게시글을 불러오는 중...</p>
    </div>

    <table v-else class="post-table">
      <thead>
        <tr>
          <th class="col-no">번호</th>
          <th class="col-type">게시판</th>
          <th class="col-title">제목</th>
          <th class="col-author">글쓴이</th>
          <th class="col-date">등록일</th>
          <th class="col-likes">추천</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="posts.length === 0">
          <td colspan="6" class="empty-state">
            게시글이 없습니다.
          </td>
        </tr>
        <PostListItem 
          v-for="post in posts" 
          :key="post.id" 
          :post="post" 
        />
      </tbody>
    </table>
  </div>
</template>

<script setup>
import PostListItem from './PostListItem.vue';

defineProps({
  posts: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.post-list-container {
  width: 100%;
}

.loading-state {
  text-align: center; 
  padding: 40px;
}

.post-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

.post-table th {
    padding: 12px 10px;
    border-bottom: 1px solid var(--border);
    text-align: center;
    vertical-align: middle;
    background-color: var(--bg-light);
    font-weight: 600;
    color: var(--text-main);
    font-size: 0.9rem;
}

.col-no { width: 8%; }
.col-type { width: 15%; }
.col-title { }
.col-author { width: 12%; }
.col-date { width: 12%; }
.col-likes { width: 8%; }

.empty-state {
  text-align: center; 
  padding: 40px; 
  color: var(--text-sub);
}
</style>