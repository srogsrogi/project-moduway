<template>
  <transition name="slide-up">
    <div v-if="comparisonStore.count > 0" class="comparison-bar">
      <div class="container bar-content">
        
        <div class="items-preview">
          <div class="count-badge">
            담은 강좌 <strong>{{ comparisonStore.count }}</strong>
          </div>
          
          <div class="thumbnails">
            <div 
              v-for="item in comparisonStore.items" 
              :key="item.id" 
              class="thumb-item"
            >
              <!-- 이미지가 없으면 기본 아이콘 -->
              <img 
                v-if="item.course_image" 
                :src="item.course_image" 
                alt="thumb"
              >
              <div v-else class="no-img">Example</div>
              <button class="btn-remove" @click.stop="comparisonStore.removeItem(item.id)">×</button>
            </div>
            
            <!-- 빈 슬롯 표시 (최대 3개) -->
            <div v-for="i in (3 - comparisonStore.count)" :key="'empty-'+i" class="thumb-item empty">
              <span>+</span>
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="btn-clear" @click="comparisonStore.clear">비우기</button>
          <router-link to="/comparisons" class="btn-compare">
            AI 분석 시작
          </router-link>
        </div>

      </div>
    </div>
  </transition>
</template>

<script setup>
import { useComparisonStore } from '@/stores/comparison';

const comparisonStore = useComparisonStore();
</script>

<style scoped>
.comparison-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: white;
  border-top: 1px solid var(--primary);
  box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
  z-index: 1000;
  padding: 15px 0;
}

.bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.items-preview {
  display: flex;
  align-items: center;
  gap: 20px;
}

.count-badge {
  font-size: 16px;
  color: var(--text-main);
}
.count-badge strong {
  color: var(--primary);
  font-size: 20px;
}

.thumbnails {
  display: flex;
  gap: 10px;
}

.thumb-item {
  width: 50px; height: 50px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: #f5f5f5;
  border: 1px solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
}
.thumb-item img {
  width: 100%; height: 100%; object-fit: cover;
}
.thumb-item.empty {
  border: 1px dashed #ccc;
  color: #ccc;
  font-size: 20px;
}
.thumb-item .no-img {
  font-size: 10px; color: #999;
}

.btn-remove {
  position: absolute;
  top: 0; right: 0;
  width: 16px; height: 16px;
  background: rgba(0,0,0,0.5);
  color: white;
  border: none;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn-clear {
  padding: 10px 20px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  color: #666;
}
.btn-compare {
  padding: 10px 30px;
  background: var(--primary);
  color: white;
  border-radius: 6px;
  font-weight: 700;
  text-decoration: none;
  display: flex; align-items: center;
}
.btn-compare:hover {
  background: var(--primary-dark);
}

/* Animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
