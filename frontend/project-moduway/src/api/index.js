import axios from 'axios';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // 백엔드 API 주소
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 요청 보낼 때 토큰이 있다면 헤더에 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터: (선택) 에러 처리 공통화 등
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 예: 401 Unauthorized 에러 시 로그아웃 처리 등
    return Promise.reject(error);
  }
);

export default api;
