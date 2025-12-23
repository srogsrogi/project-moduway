import api from './index';

// 게시판 목록 조회
export const getBoards = () => {
  return api.get('/community/boards/');
};

// 게시글 목록 조회 (게시판 ID)
export const getPostsByBoardId = (boardId, params = {}) => {
  return api.get(`/community/${boardId}/posts/`, { params });
};

// 게시글 목록 조회 (게시판 이름)
export const getPostsByBoardName = (boardName, params = {}) => {
  return api.get(`/community/${boardName}/posts/`, { params });
};

// 게시글 검색
export const searchPosts = (params) => {
  return api.get('/community/posts/search/', { params });
};

// 게시글 상세 조회
export const getPostDetail = (postId) => {
  return api.get(`/community/posts/${postId}/`);
};

// 게시글 생성
export const createPost = (boardId, data) => {
  return api.post(`/community/${boardId}/posts/`, data);
};

// 게시글 수정
export const updatePost = (postId, data) => {
  return api.put(`/community/posts/${postId}/`, data);
};

// 게시글 삭제
export const deletePost = (postId) => {
  return api.delete(`/community/posts/${postId}/`);
};

// 댓글 목록 조회
export const getComments = (postId) => {
  return api.get(`/community/posts/${postId}/comments/`);
};

// 댓글 생성
export const createComment = (postId, data) => {
  return api.post(`/community/posts/${postId}/comments/`, data);
};

// 댓글 수정
export const updateComment = (postId, commentId, data) => {
  return api.put(`/community/posts/${postId}/comments/${commentId}/`, data);
};

// 댓글 삭제
export const deleteComment = (postId, commentId) => {
  return api.delete(`/community/posts/${postId}/comments/${commentId}/`);
};

// 좋아요 토글
export const toggleLike = (postId) => {
  return api.post(`/community/posts/${postId}/likes/`);
};

// 스크랩 토글
export const toggleScrap = (postId) => {
  return api.post(`/community/posts/${postId}/scrap/`);
};
