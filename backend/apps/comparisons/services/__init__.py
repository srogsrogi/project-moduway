# backend/apps/comparisons/services/__init__.py


# apps/comparisons/services/__init__.py

"""
[설계 의도]
- services 패키지 진입점
- 각 서비스의 싱글톤 인스턴스를 외부에서 쉽게 가져올 수 있도록 export

[사용 예시]
from apps.comparisons.services import (
    get_sentiment_service,
    get_timeline_service,
    get_score_service,
    get_llm_service
)
"""

from .sentiment_service import get_sentiment_service, SentimentService
from .timeline_service import get_timeline_service, TimelineService
from .score_service import get_score_service, ScoreService
from .llm_service import get_llm_service, LLMService

__all__ = [
    'get_sentiment_service',
    'get_timeline_service',
    'get_score_service',
    'get_llm_service',
    'SentimentService',
    'TimelineService',
    'ScoreService'
    'LLMService'
]