<template>
  <div class="comment-list-container">
    <div class="comment-count">
      댓글 <span class="count-highlight">{{ comments.length }}</span>개
    </div>

    <!-- 댓글 작성 폼 (최상위) 슬롯 또는 외부 배치 가능. 
         여기서는 단순히 목록만 렌더링하고, 폼은 외부(부모)에서 처리하도록 함. 
         하지만 유저 요청은 "빈 거 작성"이므로 부모와 분리된 완전한 리스트 컴포넌트로 만듦. -->
    
    <div v-if="comments.length === 0" class="empty-comments">
      아직 댓글이 없습니다. 첫 번째 댓글을 남겨주세요!
    </div>

    <div v-else class="comment-list">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :postId="postId"
        :currentUser="currentUser"
        @delete="$emit('delete', $event)"
        @reply="$emit('reply', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import CommentItem from './CommentItem.vue';

defineProps({
  comments: {
    type: Array,
    default: () => []
  },
  postId: {
    type: [Number, String],
    required: true
  },
  currentUser: {
    type: Object,
    default: null
  }
});

defineEmits(['delete', 'reply']);
</script>

<style scoped>
.comment-list-container {
    padding-top: 20px;
}

.comment-count {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 20px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
}

.count-highlight {
    color: var(--primary-dark);
}

.empty-comments {
    text-align: center;
    padding: 30px;
    color: var(--text-sub);
    font-size: 14px;
}

.comment-list {
    /* border-top: 1px solid var(--border); */ /* comment-count 밑줄과 중복될 수 있어 제거 */
}
</style>