# apps/comparisons/ai_models/processor.py

import os
import joblib
import json
from pathlib import Path
from typing import Dict, List, Union
import logging

logger = logging.getLogger(__name__)


class SentimentProcessor:
    """
    감성분석 추론 프로세서

    [설계 의도]
    - 감성분석 모델을 매 요청마다 로드하지 않고
      애플리케이션 전체에서 1회만 메모리에 적재
    - Singleton 패턴을 사용해 성능과 자원 사용 최적화
    """

    _instance = None # 싱글톤 인스턴스
    _pipeline = None # 감성분석 파이프라인
    _metadata = None # 모델 메타데이터(버전, 정확도 등)

    def __new__(cls):
        """
        객체 생성 시점에 호출되는 메서드

        [핵심 역할]
        - SentimentProcessor가 이미 생성된 적이 있으면
          새 객체를 만들지 않고 기존 인스턴스를 반환
        """
        if cls._instance is None:
            # 새 인스턴스 생성
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        객체 초기화 메서드

        [중요 포인트]
        - __new__는 객체 생성을 제어
        - __init__은 생성된 객체의 상태를 초기화
        - 싱글톤이므로 __init__이 여러 번 호출될 수 있어
          모델 로드는 한 번만 수행하도록 조건 처리
        """
        if self._pipeline is None:
            # 모델이 로드되지 않은 경우에만 로드 수행
            self._load_model()

    def _load_model(self):
        """
        감성분석 모델 및 메타데이터 로드

        [역할]
        - joblib으로 저장된 sklearn Pipeline 로드
        - 모델 메타데이터(JSON) 함께 로드
        """
        # 현재 파일 기준 경로 설정
        base_dir = Path(__file__).resolve().parent
        # 모델 및 메타데이터 경로
        model_path = base_dir / 'sentiment_pipeline.joblib'
        metadata_path = base_dir / 'model_metadata.json'

        # 예외 처리
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            raise FileNotFoundError(
                f"감성분석 모델 파일을 찾을 수 없습니다!!! : {model_path}\n"
                f"'python manage.py train_model' 명령으로 모델을 학습해주세요."
            )

        # 모델 및 메타데이터 로드
        try:
            logger.info(f"Loading sentiment model from {model_path}")
            # joblib으로 sklearn Pipeline 로드
            self._pipeline = joblib.load(model_path)

            # 메타데이터 로드
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                logger.info(
                    f"모델 로드됨 - Ver: {self._metadata.get('version')}, "
                    f"정확도: {self._metadata.get('accuracy', 'N/A')}"
                )
            else:
                # 메타데이터 파일이 없을 경우 기본값 {}
                self._metadata = {}
                logger.warning("모델 메타데이터를 찾을 수 없습니다")

        except Exception as e:
            # 모델 로딩 중 예외 발생 시
            logger.error(f"모델 로드에 실패했습니다..: {e}")
            raise

    def analyze(self, text: str) -> Dict[str, Union[str, float]]:
        """
        단일 텍스트 감성분석

        Args:
            text: 분석할 텍스트

        Returns:
            {
                'label': 'positive' | 'negative',
                'positive_prob': 0.85,
                'negative_prob': 0.15,
                'confidence': 0.85
            }
        """
        # 예외처리 | 빈문자열 -> 기본값.
        if not text or len(text.strip()) == 0:
            return self._default_result()

        try:
            # 예측
            prediction = self._pipeline.predict([text])[0]
            probabilities = self._pipeline.predict_proba([text])[0]

            # 학습된 클래스 확인
            classes = self._pipeline.classes_

            # 확률 매핑
            if classes[0] == 'negative':
                negative_prob, positive_prob = probabilities
            else:
                positive_prob, negative_prob = probabilities

            # 신뢰도 계산 : #NOTE 우선은 단순하게, 추후 개선 고려.
            confidence = (max(positive_prob, negative_prob) - 0.5) * 2


            # 결과 반환
            return {
                'label': prediction,
                'positive_prob': float(positive_prob),
                'negative_prob': float(negative_prob),
                'confidence': float(confidence)
            }

        except Exception as e:
            logger.error(f"Sentiment analysis failed for text: {text[:50]}... Error: {e}")
            return self._default_result()

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        [설계 의도]
        - 텍스트를 하나씩 분석하지 않고
          한 번에 predict / predict_proba 호출
        - sklearn의 벡터화 성능 최대 활용

        Args:
            texts: 분석할 텍스트 리스트

        Returns:
            감성분석 결과 리스트
        """
        # 예외처리 | 빈 리스트
        if not texts:
            return []

        # 유효한 텍스트만 추출
        valid_texts = [] # 실제 분석에 쓸 텍스트
        valid_indices = [] # 원본 텍스트에서의 인덱스

        for i, text in enumerate(texts):
            if text and len(text.strip()) > 0:
                valid_texts.append(text)
                valid_indices.append(i)

        # 모두 유효하지 않으면 기본값 반환
        if not valid_texts:
            return [self._default_result() for _ in texts]

        try:
            # 배치 예측
            predictions = self._pipeline.predict(valid_texts)
            probabilities = self._pipeline.predict_proba(valid_texts)
            classes = self._pipeline.classes_

            # 결과 리스트를 기본값으로 초기화
            results = [self._default_result() for _ in texts]

            # 유효한 텍스트에 대해서만 결과 채우기
            for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
                if classes[0] == 'negative':
                    negative_prob, positive_prob = probs
                else:
                    positive_prob, negative_prob = probs

                confidence = max(positive_prob, negative_prob)

                # 원래 인덱스 위치에 결과 삽입
                results[valid_indices[i]] = {
                    'label': pred,
                    'positive_prob': float(positive_prob),
                    'negative_prob': float(negative_prob),
                    'confidence': float(confidence)
                }

            return results

        except Exception as e:
            logger.error(f"배치 감성분석에 실패했습니다.: {e}")
            return [self._default_result() for _ in texts]

    def _default_result(self) -> Dict[str, Union[str, float]]:
        """
        #NOTE
        기본 감성 결과
        - 중립이 맞을지, 다른 방안이 맞을지 고민됨. 우선은 중립.
        
        [ 사용 상황 ]
        - 분석 실패 시 반환
        - 빈 문자열 입력 시 반환
        """
        return {
            'label': 'neutral',
            'positive_prob': 0.5,
            'negative_prob': 0.5,
            'confidence': 0.5
        }

    def get_model_info(self) -> Dict:
        """
        현재 로드된 모델 정보 반환

        Returns:
            - metadata: 모델 학습 정보
            - is_loaded: 모델 로드 여부
            - classes: 분류 클래스 목록
        """
        return {
            'metadata': self._metadata,
            'is_loaded': self._pipeline is not None,
            'classes': list(self._pipeline.classes_) if self._pipeline else []
        }


def get_sentiment_processor() -> SentimentProcessor:
    """SentimentProcessor 싱글톤 인스턴스 반환"""
    return SentimentProcessor()