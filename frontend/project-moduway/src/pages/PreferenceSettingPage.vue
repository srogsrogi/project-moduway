<template>
  <div class="preference-setting-page-wrapper">
    <div class="container">
      <div class="step-one">
        <h2 class="section-title">🎯 이용 목표 설정: 가장 적합한 길을 선택하세요!</h2>
        <p class="section-description">저희 서비스는 고객님의 목표에 맞춰 가장 효과적인 맞춤형 로드맵을 제공합니다. 아래에서 현재 상황과 가장 일치하는 목표를 선택해주세요! ✨</p>

        <div 
          v-for="option in careerOptions" 
          :key="option.value" 
          class="career-option" 
          :class="{ selected: selectedCareerOption === option.value }"
          @click="selectedCareerOption = option.value"
        >
          <div class="option-header">
            <span class="icon">{{ option.icon }}</span>
            <span class="option-title">{{ option.title }}</span>
          </div>
          <div class="option-detail">{{ option.detail }}</div>
          <span class="check">✔</span>
        </div>
      </div>

      <div style="height: 40px;"></div>

      <div class="step-two">
        <h2 class="section-title">관심 분야 (직무)</h2>
        <p class="section-description">관심 있으신 직무를 모두 선택하면 직무 맞춤 강의 및 여러 가지 강의자료를 받을 수 있어요. 😉</p>

        <div class="selected-jobs-header">
          <div>
            <span class="selected-count">{{ selectedJobs.length }}</span>개 직무 선택
          </div>
          <a href="#" class="reset-link" @click.prevent="resetJobSelection">선택 재설정</a>
        </div>
        
        <div class="selected-jobs-display">
          <div v-for="job in selectedJobs" :key="job" class="job-chip">
            {{ job }} <span class="remove-chip" @click="removeJobChip(job)">×</span>
          </div>
        </div>

        <div class="job-selection-container">
          <div class="job-list-primary">
            <div v-for="job in jobOptions" :key="job" class="job-item-primary">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  :value="job" 
                  v-model="selectedJobs"
                > {{ job }}
              </label>
            </div>
          </div>
        </div>
      </div>
      
      <div style="height: 40px;"></div>

      <div class="step-three job-target-settings">
        <h2 class="section-title">직무별 선호 학습 목표</h2>
        <p class="section-description">선택하신 직무별로 목표에 맞는 맞춤 강의를 추천해 드립니다. 자세한 목표를 설정해주세요.</p>

        <div 
          v-for="job in selectedJobs" 
          :key="job" 
          class="job-target-item" 
          :data-job="job"
        >
          <h3>{{ getJobIcon(job) }} {{ job }} 학습 목표</h3>
          <div 
            v-for="(group, groupName) in learningGoals[job]" 
            :key="groupName" 
            class="hashtag-group"
          >
            <h4>{{ group.title }}</h4>
            <div class="hashtag-list">
              <div 
                v-for="tag in group.options" 
                :key="tag" 
                class="hashtag-chip" 
                :class="{ selected: form.selectedHashtags[job] && form.selectedHashtags[job][groupName] && form.selectedHashtags[job][groupName].includes(tag) }"
                @click="toggleHashtag(job, groupName, tag, group.multiple)"
              >
                {{ tag }}
              </div>
            </div>
          </div>
        </div>
        
        <p v-if="selectedJobs.length === 0" class="section-description" style="text-align: center; color: var(--text-sub);">
          선택된 직무가 없습니다. 관심 직무를 선택하면 목표를 설정할 수 있습니다.
        </p>
      </div>

      <div class="action-area">
        <button class="btn-primary" @click="savePreferences">설정 완료하고 맞춤 로드맵 확인하기</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const selectedCareerOption = ref('newbie'); // 'newbie', 'mixed', 'experienced'

const careerOptions = [
  { value: 'newbie', icon: '🐥', title: '취업/커리어 시작', detail: '현실적인 스킬로 원하는 회사에 빠르게 합격하고 싶어요. 빠르게 핵심을 배워 포트폴리오를 만들고자 합니다.' },
  { value: 'mixed', icon: '🐣', title: '커리어 전환/이직 준비', detail: '현재 직무 역량을 업그레이드하거나, 새로운 분야로 성공적인 이직을 위한 전문적인 교육이 필요해요.' },
  { value: 'experienced', icon: '🐓', title: '지식 탐구/자기 계발', detail: '특정 분야에 대한 심도 있는 지식을 쌓고 싶거나, 순수한 학습의 즐거움(취미)을 위해 서비스를 이용하고 싶어요.' },
];

const jobOptions = [
  '경영·사무', '마케팅·광고·홍보', '무역·유통', 'IT·인터넷', '생산·제조', '영업·고객상담', '건설',
];

const selectedJobs = ref([]); // Array of selected job names

const resetJobSelection = () => {
  selectedJobs.value = [];
};

// Hashtag (Learning Goals) Selection
const learningGoals = ref({
  '경영·사무': {
    'skill_level': { title: '숙련도', options: ['#초보', '#중급', '#고급'], multiple: false },
    'learning_method': { title: '학습 방식', options: ['#실습', '#이론'], multiple: false },
    'purpose': { title: '주요 목적', options: ['#시험대비', '#취업', '#승진'], multiple: true },
  },
  'IT·인터넷': {
    'skill_level': { title: '숙련도', options: ['#초보', '#중급', '#고급'], multiple: false },
    'learning_method': { title: '학습 방식', options: ['#실습', '#이론'], multiple: false },
    'purpose': { title: '주요 목적', options: ['#취업', '#창업', '#기술이해'], multiple: true },
  },
  // Add other job types here with their specific learning goals
  '마케팅·광고·홍보': {
    'skill_level': { title: '숙련도', options: ['#초보', '#중급', '#고급'], multiple: false },
    'learning_method': { title: '학습 방식', options: ['#실습', '#이론'], multiple: false },
    'purpose': { title: '주요 목적', options: ['#트렌드파악', '#실무향상'], multiple: true },
  },
  '무역·유통': { /* ... */ },
  '생산·제조': { /* ... */ },
  '영업·고객상담': { /* ... */ },
  '건설': { /* ... */ },
});

const form = ref({
  selectedCareerOption: selectedCareerOption.value,
  selectedJobs: selectedJobs.value,
  selectedHashtags: {}, // { 'IT·인터넷': { 'skill_level': ['#중급'], 'purpose': ['#취업'] } }
});

// Initialize selectedHashtags when selectedJobs changes
watch(selectedJobs, (newSelectedJobs) => {
  const newHashtags = {};
  newSelectedJobs.forEach(job => {
    if (learningGoals.value[job]) {
      newHashtags[job] = {};
      for (const groupKey in learningGoals.value[job]) {
        if (learningGoals.value[job][groupKey].multiple) {
          newHashtags[job][groupKey] = [];
        } else {
          newHashtags[job][groupKey] = []; // Single select, initialize empty
        }
      }
    }
  });
  form.value.selectedHashtags = newHashtags;
}, { immediate: true });


const toggleHashtag = (job, groupKey, tag, multiple) => {
  if (!form.value.selectedHashtags[job]) {
    form.value.selectedHashtags[job] = {};
  }
  if (!form.value.selectedHashtags[job][groupKey]) {
    form.value.selectedHashtags[job][groupKey] = [];
  }

  const currentSelection = form.value.selectedHashtags[job][groupKey];

  if (multiple) {
    // Toggle for multiple selection
    const index = currentSelection.indexOf(tag);
    if (index > -1) {
      currentSelection.splice(index, 1);
    } else {
      currentSelection.push(tag);
    }
  } else {
    // Single selection
    if (currentSelection.includes(tag)) {
      form.value.selectedHashtags[job][groupKey] = []; // Deselect if already selected
    } else {
      form.value.selectedHashtags[job][groupKey] = [tag]; // Select new tag
    }
  }
};


const getJobIcon = (jobName) => {
  // Simple mock for job icons
  if (jobName === '경영·사무') return '💼';
  if (jobName === 'IT·인터넷') return '💻';
  if (jobName === '마케팅·광고·홍보') return '📣';
  return '✨'; // Default
};


const savePreferences = () => {
  // TODO: Implement API call to save preferences
  console.log('Preferences saved:', {
    careerOption: selectedCareerOption.value,
    selectedJobs: selectedJobs.value,
    selectedHashtags: form.value.selectedHashtags,
  });
  alert('설정이 저장되었습니다. (실제 API 연동 필요)');
  // Optionally redirect to main page or user dashboard
  // router.push('/'); 
};
</script>

<style scoped>
/* Life-Learn Mockup Styles */
:root {
    --primary: #f64959;
    --primary-dark: #cc293d;
    --text-main: #111111;
    --text-sub: #666666;
    --bg-white: #ffffff;
    --bg-light: #f9f9f9;
    --border: #eeeeee;
}

.preference-setting-page-wrapper {
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
  background-color: var(--bg-white);
  color: var(--text-main);
  line-height: 1.6;
  padding: 40px 0;
  display: flex;
  justify-content: center;
}

.container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid var(--border); border-radius: 8px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

/* Common Components */
.section-title { font-size: 28px; font-weight: 700; margin-bottom: 30px; color: var(--primary-dark); }
.section-description { color: var(--text-sub); font-size: 16px; margin-bottom: 20px; }
.btn-primary { padding: 12px 24px; background-color: var(--primary); color: white; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; transition: 0.3s; width: 100%; }
.btn-primary:hover { background-color: var(--primary-dark); }
.action-area { padding-top: 30px; border-top: 1px solid var(--border); margin-top: 40px; }

/* 1. Career Info Styles */
.career-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    margin-bottom: 15px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}
.career-option:hover { border-color: var(--primary); background: var(--bg-light); }
.career-option.selected { border-color: var(--primary); background-color: #fff0f2; color: var(--primary-dark); }
.career-option .icon { margin-right: 15px; font-size: 24px; }
.career-option .check { color: var(--primary); font-size: 24px; }
.career-option:not(.selected) .check { display: none; }
.career-option.selected .check { display: block; }
.option-header { display: flex; align-items: center; }
.option-title { margin-right: 15px; }
.option-detail { font-size: 14px; font-weight: 400; color: var(--text-sub); flex-grow: 1; margin-left: 20px; }

/* 2. Job Selection Styles (Modified for Multi-Select) */
.selected-jobs-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.selected-count { font-size: 18px; font-weight: 600; color: var(--primary-dark); margin-right: 5px; }
.reset-link { font-size: 14px; color: var(--primary); cursor: pointer; }

.job-selection-container {
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 30px;
}
.job-list-primary {
    max-height: 400px;
    overflow-y: auto;
    padding: 15px;
}

.job-item-primary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 10px;
    margin-bottom: 5px;
    border-radius: 4px;
    cursor: pointer;
    transition: 0.1s;
}
.job-item-primary:hover { background: var(--bg-light); }

.checkbox-label { font-size: 16px; font-weight: 500; display: flex; align-items: center; cursor: pointer; }
.checkbox-label input[type="checkbox"] { margin-right: 10px; width: 18px; height: 18px; accent-color: var(--primary); }

/* New: Selected Jobs Display */
.selected-jobs-display {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 15px 0;
    margin-bottom: 20px;
    border-bottom: 1px dashed var(--border);
    min-height: 30px;
}
.job-chip {
    background: var(--primary);
    color: white;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
}
.remove-chip {
    margin-left: 8px;
    cursor: pointer;
    font-weight: bold;
    font-size: 16px;
}

/* 3. Hashtag Selection Styles (Modified for Job-Specifics) */
.job-target-settings { margin-top: 40px; }
.job-target-item { 
    border: 1px solid #ffcccc; 
    background: #fffafa; 
    padding: 20px; 
    margin-bottom: 30px; 
    border-radius: 8px;
}
.job-target-item h3 { 
    font-size: 20px; 
    font-weight: 700; 
    color: var(--primary-dark); 
    margin-bottom: 20px; 
    border-bottom: 2px solid #ffcccc; 
    padding-bottom: 10px;
}

.hashtag-group { margin-bottom: 25px; }
.hashtag-group h4 { font-size: 16px; color: var(--text-main); margin-bottom: 10px; border-left: 4px solid var(--primary); padding-left: 10px; font-weight: 600; }
.hashtag-list { display: flex; flex-wrap: wrap; gap: 10px; }
.hashtag-chip {
    padding: 8px 15px;
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 15px;
    cursor: pointer;
    transition: 0.2s;
}
.hashtag-chip:hover { border-color: var(--primary); }
.hashtag-chip.selected {
    background-color: var(--primary);
    color: white;
    border-color: var(--primary);
}
</style>