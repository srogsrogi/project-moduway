import api from './index';

// 로그인
export const login = (credentials) => {
  return api.post('/accounts/login/', credentials);
};

// 구글 소셜 로그인
export const googleLogin = (accessToken) => {
  return api.post('/accounts/google/', { access_token: accessToken });
};

// 회원가입
export const register = (userData) => {
  return api.post('/accounts/registration/', userData);
};

// 로그아웃
export const logout = () => {
  return api.post('/accounts/logout/');
};

// 사용자 정보 조회
export const getUserInfo = () => {
  return api.get('/accounts/user/');
};

// 비밀번호 변경
export const changePassword = (passwordData) => {
  return api.post('/accounts/mypage/profile/password/change/', passwordData);
};
