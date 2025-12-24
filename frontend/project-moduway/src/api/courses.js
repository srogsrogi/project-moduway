import api from './index';

// 강좌 상세 조회
export const getCourseDetail = (courseId) => {
  return api.get(`/courses/${courseId}/`);
};

// 강좌 리뷰 목록 조회
export const getCourseReviews = (courseId) => {
  return api.get(`/courses/${courseId}/reviews/`);
};

// AI 추천 강좌 조회
export const getRecommendedCourses = (courseId) => {
  return api.get(`/courses/${courseId}/recommendations/`);
};

// 의미 기반 강좌 검색
export const searchSemanticCourses = (query) => {
  return api.get(`/courses/search/semantic/`, { params: { query } });
};
