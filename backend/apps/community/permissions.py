# backend/apps/community/permissions.py

from rest_framework import permissions
    
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    [설계의도]
    - 비회원은 조회만, 작성자는 수정/삭제 가능한
    - 커스텀 객체 수준 퍼미션 클래스 (객체 단위로 권한을 제어했다.)

    [상세고려사항]
    - 게시글/댓글 공통 권한 정책으로 재사용 가능
    - SAFE_METHODS에 속하는 요청(GET, HEAD, OPTIONS)은 누구나 접근 가능
    - 그 외의 요청(POST, PUT, DELETE 등)은 객체의 작성자만 허용
    """
    def has_object_permission(self, request, view, obj):
        # 읽기 요청(GET, HEAD, OPTIONS)은 모두 허용
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 쓰기 요청은 객체의 author와 요청 user가 동일할 때만 허용
        return obj.author == request.user
    

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    [설계의도]
    - 비회원은 조회만, 회원은 모든 행위 허용하는
    - 커스텀 퍼미션 클래스

    [상세고려사항]
    - 게시글/댓글 공통 권한 정책으로 재사용 가능
    - SAFE_METHODS에 속하는 요청(GET, HEAD, OPTIONS)은 누구나 접근 가능
    - 그 외의 요청(POST, PUT, DELETE 등)은 인증된 사용자만 허용
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated