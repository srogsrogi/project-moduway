<template>
  <RouterLink :to="`/courses/${id}`" class="course-card-link">
    <div class="course-card">
      <div class="card-thumb">
        <span class="badge" :style="{ backgroundColor: badgeColor }">{{ status }}</span>
        <img v-if="thumbnail" :src="thumbnail" :alt="title" />
        <div v-else class="placeholder-thumb">THUMBNAIL</div>
      </div>
      <div class="card-body">
        <span class="uni-name">{{ university }}</span>
        <h3 class="course-title">{{ title }}</h3>
        <div class="course-info">
          <span>{{ instructor }}</span>
          <span>{{ period }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
defineProps({
  id: { type: [Number, String], required: true },
  title: { type: String, required: true },
  university: { type: String, required: true },
  instructor: { type: String, required: true },
  period: { type: String, required: true },
  status: { type: String, default: '접수중' },
  badgeColor: { type: String, default: 'var(--primary-dark)' },
  thumbnail: { type: String, default: '' }
});
</script>

<style scoped>
.course-card-link { text-decoration: none; color: inherit; display: block; }
.course-card { background: white; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: 0.3s; position: relative; cursor: pointer; }
.course-card:hover { box-shadow: 0 10px 20px rgba(0,0,0,0.08); transform: translateY(-5px); border-color: #ffdce0; }

.card-thumb { height: 160px; background-color: #eee; position: relative; overflow: hidden; }
.card-thumb img { width: 100%; height: 100%; object-fit: cover; }
.placeholder-thumb { width: 100%; height: 100%; background: #f6f6f6; display: flex; align-items: center; justify-content: center; color: #ccc; }

.badge { position: absolute; top: 12px; left: 12px; background: var(--primary-dark); color: white; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; z-index: 1; }

.card-body { padding: 20px; }
.uni-name { font-size: 13px; color: var(--text-sub); margin-bottom: 8px; display: block; }
.course-title { font-size: 18px; font-weight: 700; line-height: 1.4; margin-bottom: 12px; height: 50px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-top: 0; color: var(--text-main); }
.course-info { font-size: 13px; color: #888; display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 15px; margin-top: 15px; }
</style>