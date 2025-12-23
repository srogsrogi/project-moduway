<template>
  <tr>
    <td class="col-no">{{ post.id }}</td>
    <td class="col-type">{{ getBoardKoreanName(post.board_name) }}</td>
    <td class="col-title">
      <router-link :to="`/community/posts/${post.id}`">
        {{ post.title }}
        <span v-if="post.comments_count > 0" class="comment-count">
          [{{ post.comments_count }}]
        </span>
      </router-link>
    </td>
    <td class="col-author">{{ post.author.name }}</td>
    <td class="col-date">{{ formatDate(post.created_at) }}</td>
    <td class="col-likes">{{ post.likes_count }}</td>
  </tr>
</template>

<script setup>
const props = defineProps({
  post: {
    type: Object,
    required: true
  }
});

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
    return `${cat} - ${type}`;
  }
  return boardName;
};

// 날짜 포맷팅 (YYYY.MM.DD)
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
};
</script>

<style scoped>
td {
    padding: 12px 10px;
    border-bottom: 1px solid var(--border);
    text-align: center;
    vertical-align: middle;
    font-size: 0.95rem;
    color: var(--text-main);
}

.col-no { width: 8%; color: var(--text-sub); }
.col-type { width: 15%; font-weight: 600; color: var(--primary-dark); }
.col-title { 
  text-align: left; 
  padding-left: 15px; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
}
.col-title a { 
  text-decoration: none; 
  color: inherit; 
  display: block; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
}
.col-author { width: 12%; }
.col-date { width: 12%; color: var(--text-sub); }
.col-likes { width: 8%; color: var(--primary); }

.comment-count {
  color: var(--primary); 
  margin-left: 4px;
  font-size: 0.9em;
  font-weight: bold;
}

tr:hover {
    background-color: var(--primary-light);
}
</style>