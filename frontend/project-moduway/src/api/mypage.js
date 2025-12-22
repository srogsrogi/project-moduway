import api from './index';

// 마이페이지 대시보드 통계 조회
export const getDashboardStats = () => {
  return api.get('/mypage/dashboard/stats/');
};

// 최근 학습 강좌 조회
export const getRecentCourse = () => {
  return api.get('/mypage/courses/recent/');
};

// 수강 목록 조회 (상태별)
export const getMyCourses = (status) => {
  return api.get('/mypage/courses/', { params: { status } });
};

// 찜 목록 조회
export const getWishlist = () => {
  return api.get('/mypage/wishlist/');
};

// 찜 추가
export const addWishlist = (courseId) => {
  return api.post(`/mypage/wishlist/${courseId}/`);
};

// 찜 삭제
export const removeWishlist = (courseId) => {
  return api.delete(`/mypage/wishlist/${courseId}/`);
};

// 수강평 등록/수정
export const saveReview = (courseId, reviewData) => {
  return api.post(`/mypage/courses/${courseId}/rating/`, reviewData);
};

// 수강평 삭제
export const deleteReview = (courseId) => {
  return api.delete(`/mypage/courses/${courseId}/rating/`);
};

// 커뮤니티 활동 통계 조회
export const getCommunityStats = () => {
  return api.get('/mypage/community/stats/');
};

// 내가 쓴 글 목록 조회
export const getMyPosts = () => {
  return api.get('/mypage/community/posts/');
};

// 내가 쓴 댓글 목록 조회
export const getMyComments = () => {
  return api.get('/mypage/community/comments/');
};

// 스크랩 목록 조회
export const getMyScraps = () => {
  return api.get('/mypage/scraps/');
};

// 프로필 정보 조회
export const getProfile = () => {
  return api.get('/mypage/profile/');
};

// 프로필 정보 수정
export const updateProfile = (profileData) => {
  return api.put('/mypage/profile/', profileData);
};
