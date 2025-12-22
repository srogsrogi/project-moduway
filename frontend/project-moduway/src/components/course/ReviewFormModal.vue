<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <h2>수강평 작성하기</h2>
        <button class="btn-close" @click="$emit('close')">×</button>
      </div>
      
      <div class="modal-body">
        <div class="rating-selector">
          <p class="label">강좌는 어떠셨나요? 평점을 선택해주세요.</p>
          <div class="stars">
            <span 
              v-for="i in 5" 
              :key="i" 
              class="star-btn" 
              :class="{ active: i <= form.rating }"
              @click="form.rating = i"
            >★</span>
          </div>
        </div>

        <div class="review-input">
          <p class="label">상세한 후기를 남겨주세요. (최소 100자)</p>
          <textarea 
            v-model="form.review_text" 
            placeholder="강좌의 장점, 보완할 점 등 다른 수강생들에게 도움이 될 내용을 100자 이상 자유롭게 작성해 주세요."
            rows="8"
          ></textarea>
          <div class="char-count" :class="{ error: form.review_text.length < 100 }">
            {{ form.review_text.length }} / 100자 이상
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">취소</button>
        <button 
          class="btn-submit" 
          :disabled="!isValid || isSubmitting"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '저장 중...' : '수강평 등록하기' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';

const props = defineProps({
  initialData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'submit']);

// rating 기본값을 0으로 설정 (선택 강제)
const form = reactive({
  rating: props.initialData?.rating || 0,
  review_text: props.initialData?.review_text || ''
});

const isSubmitting = ref(false);

const isValid = computed(() => {
  // 별점이 1점 이상 선택되어야 하고, 텍스트가 100자 이상이어야 함
  return form.rating > 0 && form.review_text.trim().length >= 100;
});

const handleSubmit = async () => {
  if (!isValid.value) return;
  isSubmitting.value = true;
  try {
    emit('submit', { ...form });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  width: 100%;
  max-width: 600px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center;
}

.modal-header h2 { font-size: 20px; font-weight: 800; margin: 0; }
.btn-close { background: none; border: none; font-size: 32px; color: #999; cursor: pointer; }

.modal-body { padding: 32px; }

.label { font-weight: 700; color: var(--text-main); margin-bottom: 12px; font-size: 15px; }

.rating-selector { margin-bottom: 32px; text-align: center; }
.stars { display: flex; justify-content: center; gap: 8px; }
.star-btn { font-size: 40px; color: #ddd; cursor: pointer; transition: 0.2s; }
.star-btn.active { color: #ffb800; }

.review-input textarea {
  width: 100%;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 12px;
  font-family: inherit;
  font-size: 15px;
  resize: none;
  background: #f9f9f9;
}
.review-input textarea:focus { outline: none; border-color: var(--primary); background: white; }

.char-count { text-align: right; font-size: 12px; color: #666; margin-top: 8px; }
.char-count.error { color: var(--primary); }

.modal-footer {
  padding: 24px;
  background: #f9f9f9;
  display: flex; justify-content: flex-end; gap: 12px;
}

.btn-cancel {
  padding: 12px 24px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}

.btn-submit {
  padding: 12px 32px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}
.btn-submit:disabled { background: #ccc; cursor: not-allowed; }
</style>