import { ref, computed, watch } from 'vue';

// 로컬 스토리지 키
const STORAGE_KEY = 'comparison_items';

// 초기 상태 로드
const storedItems = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
const items = ref(storedItems);

// 상태 변경 시 로컬 스토리지 저장
watch(items, (newItems) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newItems));
}, { deep: true });

// Getter: 담긴 개수
const count = computed(() => items.value.length);

// Action: 강좌 담기
const addItem = (course) => {
  // 이미 담긴 강좌인지 확인
  if (items.value.find(item => item.id === course.id)) {
    alert('이미 분석함에 담긴 강좌입니다.');
    return;
  }
  // 최대 3개 제한
  if (items.value.length >= 3) {
    alert('최대 3개 강좌까지 분석할 수 있습니다.');
    return;
  }
  
  // 필요한 정보만 추출해서 저장 (가상 분석 데이터 생성을 위해 최소 정보 + 원본)
  // 실제로는 여기서 course 객체 전체를 저장하거나, ID만 저장하고 페이지에서 상세 조회
  // 프로토타입 편의를 위해 전체 객체 저장
  items.value.push(course);
};

// Action: 강좌 빼기
const removeItem = (courseId) => {
  items.value = items.value.filter(item => item.id !== courseId);
};

// Action: 전체 비우기
const clear = () => {
  items.value = [];
};

// Action: 담겨있는지 확인
const isAdded = (courseId) => {
  return items.value.some(item => item.id === courseId);
};

export const useComparisonStore = () => {
  return {
    items,
    count,
    addItem,
    removeItem,
    clear,
    isAdded,
  };
};
