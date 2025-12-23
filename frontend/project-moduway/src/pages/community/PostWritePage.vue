<template>
  <div class="write-main">
    <div class="write-container">
      <router-link to="/community" class="link-back">← 커뮤니티 목록으로</router-link>

      <div class="write-box">
        <h1>{{ isEditMode ? '게시글 수정' : '게시글 작성' }}</h1>

        <form @submit.prevent="handleSubmit">
          
          <div class="form-group">
            <label>게시판 선택</label>
            <div class="category-select">
              <select v-model="form.mainCategory" required @change="handleMainCategoryChange">
                <option value="" disabled>-- 대분류 --</option>
                <option v-for="cat in mainCategories" :key="cat.value" :value="cat.value">
                  {{ cat.label }}
                </option>
              </select>
              
              <select v-model="form.subCategory" :disabled="form.mainCategory === 'notice'" required>
                <option value="" disabled>-- 소분류 (유형) --</option>
                <option value="talk">시시콜콜 (소통방)</option>
                <option value="review">왁자지껄 (강의후기)</option>
                <option value="qna">주고받고 (강의질문방)</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="postTitle">제목</label>
            <input 
              type="text" 
              id="postTitle" 
              class="form-control" 
              placeholder="제목을 입력해주세요." 
              v-model="form.title" 
              required
            >
          </div>

          <div class="form-group">
            <label for="postContent">내용</label>
            <!-- WYSIWYG 에디터 대체용 textarea -->
            <textarea 
              id="postContent" 
              class="form-control editor-placeholder" 
              placeholder="내용을 입력해주세요." 
              v-model="form.content"
              required
            ></textarea>
          </div>

          <div class="action-buttons">
            <button type="button" class="btn btn-outline" @click="$router.back()">취소</button>
            <button type="submit" class="btn btn-primary">{{ isEditMode ? '수정하기' : '등록하기' }}</button>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createPost, updatePost, getPostDetail } from '@/api/community';

const route = useRoute();
const router = useRouter();

const isEditMode = computed(() => !!route.params.id);

const form = ref({
  mainCategory: '',
  subCategory: '',
  title: '',
  content: ''
});

const mainCategories = [
  { value: 'humanity', label: '인문' },
  { value: 'social', label: '사회' },
  { value: 'education', label: '교육' },
  { value: 'engineering', label: '공학' },
  { value: 'natural', label: '자연' },
  { value: 'medical', label: '의약' },
  { value: 'arts_pe', label: '예체능' },
  { value: 'convergence', label: '융·복합' },
  { value: 'etc', label: '기타' },
  { value: 'notice', label: '공지사항' },
];

const handleMainCategoryChange = () => {
  if (form.value.mainCategory === 'notice') {
    form.value.subCategory = '';
  }
};

const handleSubmit = async () => {
  if (!form.value.mainCategory) {
    alert('게시판 대분류를 선택해주세요.');
    return;
  }
  if (!form.value.subCategory && form.value.mainCategory !== 'notice') {
    alert('게시판 소분류를 선택해주세요.');
    return;
  }

  // 게시판 식별자 생성 (예: humanity_talk)
  let boardName = form.value.mainCategory;
  if (form.value.mainCategory !== 'notice') {
    boardName = `${form.value.mainCategory}_${form.value.subCategory}`;
  }

  try {
    const postData = {
      title: form.value.title,
      content: form.value.content,
    };
    
    if (isEditMode.value) {
      await updatePost(route.params.id, postData);
      alert('게시글이 수정되었습니다.');
    } else {
      await createPost(boardName, postData);
      alert('게시글이 등록되었습니다.');
    }
    
    router.push('/community');
  } catch (error) {
    console.error('게시글 저장 실패:', error);
    alert('게시글 저장에 실패했습니다.');
  }
};

const fetchPostData = async (id) => {
  try {
    const response = await getPostDetail(id);
    const post = response.data;
    
    form.value.title = post.title;
    form.value.content = post.content;
    
    // board.name (예: "humanity_talk" 또는 "자유게시판") 파싱 로직 필요
    if (post.board && post.board.name) {
      const parts = post.board.name.split('_');
      if (parts.length >= 2) {
        form.value.mainCategory = parts[0];
        form.value.subCategory = parts[1];
      } else if (parts[0] === 'notice') {
        form.value.mainCategory = 'notice';
      }
    }
  } catch (error) {
    console.error('게시글 불러오기 실패:', error);
    alert('게시글 정보를 불러오지 못했습니다.');
    router.push('/community');
  }
};

onMounted(() => {
  if (isEditMode.value) {
    fetchPostData(route.params.id);
  } else {
    // For new post, check query parameters
    const mainCatParam = route.query.mainCat;
    const subCatParam = route.query.subCat;

    if (mainCatParam) {
      form.value.mainCategory = mainCatParam;
      if (mainCatParam === 'notice') {
        form.value.subCategory = ''; // Disable subcategory for notice
      } else if (subCatParam) {
        form.value.subCategory = subCatParam;
      }
    }
  }
});
</script>

<style scoped>
/* 게시글 작성 스타일 */
.write-main { 
    padding: 40px 0;
    display: flex;
    justify-content: center;
}

.write-container {
    width: 100%;
    max-width: 900px; 
    padding: 0 20px;
}

.link-back { color: var(--text-sub); font-size: 14px; margin-bottom: 15px; display: block; }

.write-box {
    background-color: var(--bg-white);
    padding: 30px 40px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    border: 1px solid var(--border); /* Added border for better visibility if shadow is subtle */
}

.write-box h1 {
    font-size: 28px;
    font-weight: 800;
    color: var(--primary-dark);
    border-bottom: 2px solid var(--primary);
    padding-bottom: 15px;
    margin-bottom: 30px;
}

/* 입력 폼 스타일 */
.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
    color: var(--text-main);
}

.form-control {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s;
    font-family: inherit; /* textarea 폰트 상속 */
}

.form-control:focus {
    border-color: var(--primary);
}

/* 카테고리 선택 */
.category-select {
    display: flex;
    gap: 20px;
}

.category-select select {
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 15px;
    outline: none;
}

/* 내용 (에디터 영역) */
.editor-placeholder {
    min-height: 400px;
    resize: vertical;
}

/* 첨부 파일 */
.file-upload-box {
    border: 1px dashed var(--border);
    border-radius: 6px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s;
    margin-top: 10px;
    display: block;
}
.file-upload-box:hover {
    border-color: var(--primary);
    background-color: var(--primary-light);
}
.file-upload-box input[type="file"] {
    display: none;
}
.file-info {
    font-size: 13px;
    color: var(--text-sub);
    margin-top: 5px;
}

/* 하단 버튼 */
.action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 30px;
}
.action-buttons .btn {
    padding: 12px 30px;
}

/* 반응형 */
@media (max-width: 768px) {
    .write-box {
        padding: 20px;
    }
    .category-select {
        flex-direction: column;
        gap: 10px;
    }
    .category-select select {
        width: 100%;
    }
    .action-buttons {
        justify-content: space-between;
    }
}
</style>