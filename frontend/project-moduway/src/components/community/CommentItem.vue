<template>
  <div class="comment-item" :style="{ marginLeft: depth * 30 + 'px' }">
    <div class="comment-meta">
      <div class="profile-img"></div>
      <span class="nickname">{{ comment.author.name }}</span>
      <span class="date">{{ formatDate(comment.created_at) }}</span>
    </div>
    <div class="comment-content">{{ comment.content }}</div>
    <div class="comment-actions">
      <button @click="$emit('reply', comment)" class="action-btn">답글</button>
      <button v-if="isAuthor" @click="$emit('delete', comment.id)" class="action-btn delete">삭제</button>
    </div>

    <!-- 대댓글 재귀 -->
    <CommentItem
      v-for="reply in comment.replies"
      :key="reply.id"
      :comment="reply"
      :postId="postId"
      :currentUser="currentUser"
      :depth="depth + 1"
      @delete="$emit('delete', $event)"
      @reply="$emit('reply', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  comment: Object,
  postId: Number,
  currentUser: Object,
  depth: { type: Number, default: 0 }
});

defineEmits(['delete', 'reply']);

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}.${month}.${day} ${hours}:${minutes}`;
};

const isAuthor = computed(() => {
  return props.currentUser && props.currentUser.id === props.comment.author.id;
});
</script>

<style scoped>
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
</style>
