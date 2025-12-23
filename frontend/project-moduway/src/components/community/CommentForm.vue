<template>
  <div class="comment-input-box">
    <div v-if="replyTo" class="reply-info">
      <span>@{{ replyTo.author.name }}님에게 답글 작성 중</span>
      <button @click="$emit('cancel')" class="cancel-btn">취소</button>
    </div>
    <textarea
      :placeholder="placeholderText"
      v-model="content"
      @keydown.ctrl.enter="handleSubmit"
    ></textarea>
    <div class="comment-submit">
      <button class="btn btn-primary" :disabled="!content.trim()" @click="handleSubmit">
        {{ replyTo ? '답글 등록' : '댓글 등록' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  replyTo: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['submit', 'cancel']);

const content = ref('');

// 답글 대상이 변경되면 입력창 초기화 또는 포커스 처리 등을 할 수 있음
// 여기서는 멘션 텍스트 자동 삽입 등은 하지 않고 단순 유지
watch(() => props.replyTo, (newVal) => {
  if (newVal) {
    // 답글 모드로 진입 시 로직 (필요하면 추가)
    // content.value = ''; 
  }
});

const placeholderText = computed(() => {
  return props.replyTo 
    ? '답글을 입력하세요...' 
    : '댓글을 남겨보세요. 매너 있는 댓글 문화 부탁드립니다.';
});

const handleSubmit = () => {
  if (!content.value.trim()) return;
  
  emit('submit', content.value);
  content.value = ''; // 제출 후 초기화
};
</script>

<style scoped>
.comment-input-box {
    margin-bottom: 20px;
}

.comment-input-box textarea {
    width: 100%;
    min-height: 80px;
    padding: 15px;
    border: 1px solid var(--border);
    border-radius: 6px;
    resize: vertical;
    outline: none;
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s;
}

.comment-input-box textarea:focus {
    border-color: var(--primary);
}

.comment-submit {
    display: flex;
    justify-content: flex-end;
    margin-top: 10px;
}

.comment-submit .btn {
    padding: 8px 15px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
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
</style>