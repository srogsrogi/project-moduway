# apps/comparisons/management/commands/train_model.py

import os
import json
import joblib
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pandas.errors import EmptyDataError


# 한국어 형태소 분석기 - 토크나이저로 활용
from kiwipiepy import Kiwi
# TF-IDF 벡터라이저
from sklearn.feature_extraction.text import TfidfVectorizer
# 선형 분류 모델(로지스틱 회귀)
from sklearn.linear_model import LogisticRegression
# 전처리 + 모델링
from sklearn.pipeline import Pipeline
# 데이터 분할 및 평가
from sklearn.model_selection import train_test_split, cross_val_score
# 평가 지표
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

DEFAULT_DATA_PATH = Path(settings.BASE_DIR) / "apps" / "comparisons" / "fixtures" / "sentiment_training_data.csv"
DEFAULT_MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "comparisons" / "ai_models"


# Kiwi 토크나이저
# 전역 인스턴스로 생성
# pickle 이슈 방지 목적
kiwi = Kiwi()

def kiwi_tokenizer(text):
    """
    Kiwi 형태소 분석기를 사용한 토크나이징 함수

    [역할]
    - 명사(N), 동사(V), 형용사(VA), 어근(XR) 등 의미 있는 품사만 추출

    [품사 필터]
    - N: 명사
    - V: 동사
    - M: 수식언 (형용사 포함)
    - XR: 어근
    """
    try:
        tokens = kiwi.tokenize(text)
        return [
            t.form for t in tokens
            # 필터링
            if t.tag.startswith(('N', 'V', 'M', 'XR'))  # 명사, 동사, 수식언, 어근
        ]
    except Exception:
        # fallback: 공백 기준 split | 최후의 안전장치
        return text.split()  # fallback


class Command(BaseCommand):
    """
    [설계 의도]
    - 한국어 강의 후기(리뷰) 텍스트를 대상으로 하는 감성분석 모델을
      로컬/개발 환경에서 빠르게 학습하고, 추론 서버(Processor)에서 바로 사용할 수 있게
      Pipeline(joblib) + Metadata(json) 형태로 저장하기 위함
    - Django management command로 구현해 CI/배포 파이프라인 또는 팀 개발 환경에서
      `python manage.py train_model` 하나로 재학습/교체가 가능하도록 함

    [상세 고려사항]
    - 학습/추론 일관성을 위해 전처리(TF-IDF)와 모델(LogisticRegression)을
      sklearn Pipeline으로 묶어 joblib 저장
    - 한국어 특성을 반영하기 위해 Kiwi 형태소 분석 기반 tokenizer를 사용하고,
      의미 있는 품사만 필터링하여 노이즈를 줄임
    - 데이터 검증(필수 컬럼/결측/라벨 검증)을 선행하여 학습 중단을 조기에 발생시키고,
      잘못된 데이터로 모델이 저장되는 상황을 방지
    - 클래스 불균형 가능성을 고려해 class_weight='balanced'를 사용
    - 결과 재현성을 위해 random_state를 고정
    """
    help = '감성분석 모델 학습 및 저장'

    def add_arguments(self, parser):
        """
        manage.py train_model 실행 시 받을  CLI 옵션을 정리하는 메서드

        [설계 의도]
        - 데이터 경로, 분할 비율, 특징 생성(min_df, ngram), 모델 규제(C),
          평가(cv fold)를 CLI 옵션으로 노출해 실험/튜닝을 빠르게 반복하기 위함

        [옵션 설명]
        --data: 학습 데이터 CSV 파일 경로
        --test-size: 테스트 데이터 비율 (0.0 ~ 1.0)
        --min-df: TF-IDF의 최소 문서 빈도
        --ngram: N-gram 최대 크기
        --C: LogisticRegression의 정규화 강도
        --cv: 교차 검증 fold 수
        """
        # 학습 데이터 CSV 파일 경로
        parser.add_argument(
            '--data',
            type=str,
            default=str(DEFAULT_DATA_PATH),
            help='학습 데이터 CSV 파일 경로'
        )

        # 테스트 데이터 비율
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='테스트 데이터 비율 (0.0 ~ 1.0)'
        )

        # TF-IDF 최소 문서 빈도
        parser.add_argument(
            '--min-df',
            type=int,
            default=3,
            help='최소 문서 빈도 (TF-IDF)'
        )

    
        # N-gram 최대 크기
        parser.add_argument(
            '--ngram',
            type=int,
            default=2,
            help='N-gram 최대 크기 (1 또는 2 권장)'
        )

        # LogisticRegression의 정규화 강도
        parser.add_argument(
            '--C',
            type=float,
            default=1.0,
            help='LogisticRegression의 정규화 강도 (C 파라미터)'
        )

        # 교차 검증 fold 수
        parser.add_argument(
            '--cv',
            type=int,
            default=5,
            help='교차 검증 fold 수'
        )

    def _load_csv_or_fail(self, data_path: Path) -> pd.DataFrame:
        """CSV 존재/빈파일/파싱 불가를 CommandError로 변환"""
        if not data_path.exists():
            raise CommandError(f"학습 데이터 파일이 없습니다: {data_path}")

        if data_path.stat().st_size == 0:
            raise CommandError(f"학습 데이터 파일이 비어있습니다(0 bytes): {data_path}")

        try:
            return pd.read_csv(data_path, encoding="utf-8-sig")
        except EmptyDataError:
            raise CommandError(f"CSV 파싱 실패(헤더/컬럼 없음): {data_path}")
    
    def handle(self, *args, **options):
        """
        메인 단계

        [설계 의도]
        - “학습 전체 플로우”를 단일 커맨드로 수행해,
          모델 재학습/교체 작업을 반복 가능하고 재현성 있게 만든다.

        [단계]
        1. 데이터 로드
        2. 데이터 검증 | 결측지 제거, 라벨 검증
        3. 데이터 분할 (학습/테스트)
        4. 모델 구축 및 학습 | Kiwi 토크나이저(전역)이용, 파이프라인 구축, 학습
        5. 모델 평가 | 테스트데이터예측 -> 정확도, 교차검증, 분류리포트, 혼동행렬
        6. 모델 저장 | joblib, 메타데이터 JSON
        """
        # 시작 안내 출력
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('감성분석 모델 학습 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 1. 데이터 로드
        data_path = Path(options['data']) # exists 체크를 위해 path 객체로 변환
        self.stdout.write(f'\n[1/6] 데이터 로드: {data_path}')

        # 파일이 없으며 중단.
        if not data_path.exists():
            raise CommandError(f'데이터 파일을 찾을 수 없습니다: {data_path}')

        # CSV 파일 로드
        df = self._load_csv_or_fail(data_path)
        self.stdout.write(f'  ✓ 총 {len(df)}개 데이터 로드')
        self.stdout.write(f'  ✓ 긍정: {sum(df["label"] == "positive")}개')
        self.stdout.write(f'  ✓ 부정: {sum(df["label"] == "negative")}개')

        # 2. 데이터 검증 | 결측지 제거, 라벨 검증
        self.stdout.write('\n[2/6] 데이터 검증')

        # 필수 컬럼 정의
        required_columns = ['content', 'label']
        # 놓친 컬럼 있나
        missing_columns = [col for col in required_columns if col not in df.columns]

        # 있으면
        if missing_columns:
            raise CommandError(
                f'필수 컬럼이 없습니다: {missing_columns}\n'
                f'CSV 파일은 "content"와 "label" 컬럼을 포함해야 합니다.'
            )

        # 결측치 제거 전 길이 저장 : 안내용
        original_len = len(df)

        # 둘 중 하나라도 결측치면 제거
        df = df.dropna(subset=['content', 'label'])

        # 제거된 행이 있으면 안내
        if len(df) < original_len:
            self.stdout.write(
                self.style.WARNING(
                    f'  ! 결측치 {original_len - len(df)}개를 제거하였습니다.'
                )
            )

        # 라벨 검증
        # 허용 라벨 set 정의
        valid_labels = {'positive', 'negative'}
        # 데이터프레임에 존재하는 라벨 중 유효하지 않은 것들
        invalid_labels = set(df['label'].unique()) - valid_labels

        # 허용되지 않은 라벨이 있으면 중단
        if invalid_labels:
            raise CommandError(
                f'유효하지 않은 라벨: {invalid_labels}\n'
                f'라벨은 "positive" 또는 "negative"만 허용됩니다.'
            )

        self.stdout.write('  ✓ 데이터 검증 완료')

        # 3. 데이터 분할
        self.stdout.write('\n[3/6] 학습/테스트 데이터 분할')

        X = df['content'] # 텍스트
        y = df['label'] # 라벨

        test_size = options['test_size']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y  # 클래스 비율 유지
        )

        # 분할 결과 출력
        self.stdout.write(f'  ✓ 학습 데이터: {len(X_train)}개')
        self.stdout.write(f'  ✓ 테스트 데이터: {len(X_test)}개')

        # 4. 모델 구축 및 학습
        self.stdout.write('\n[4/6] 모델 학습')

        # 파이프라인 구축 | TF-IDF -> LogisticRegression
        pipeline = Pipeline([
            # 1) TF-IDF 벡터라이저: 텍스트를 수치 벡터로 변환
            ('tfidf', TfidfVectorizer(
                tokenizer=kiwi_tokenizer,                 # 사용자 정의 토크나이저 사용
                ngram_range=(1, options['ngram']),         # unigram~ngram
                min_df=options['min_df'],                  # 너무 희귀한 단어 제거(노이즈 감소)
                max_features=5000,                         # 상위 5000개 특징만 사용(메모리/속도 절약)
                sublinear_tf=True,                         # TF를 log 스케일로 완화(긴 문장 영향 완화)
                token_pattern=None                         # tokenizer를 직접 쓰면 반드시 None으로 두는 게 안전
            )),     
            # 2) 분류기: 로지스틱 회귀
            ('clf', LogisticRegression(
                C=options['C'],               # 규제 강도 조절(값이 클수록 규제 약함)
                max_iter=1000,                # 수렴이 느릴 때 대비
                class_weight='balanced',      # 클래스 불균형 시 자동 가중치 보정
                random_state=42,              # 재현성
                solver='lbfgs'                # 다중 클래스도 잘 되는 기본 solver
            ))
        ])

        # 학습
        self.stdout.write('  ✓ 학습 진행 중...')
        pipeline.fit(X_train, y_train) # tfidf + clf
        self.stdout.write(self.style.SUCCESS('  ✓ 학습 완료'))

        # 5. 모델 평가
        self.stdout.write('\n[5/6] 모델 평가')

        # 테스트 데이터 예측
        y_pred = pipeline.predict(X_test)

        # 정확도 계산 | (맞춘 개수/전체 개수) | #NOTE 불균형 데이터셋이 아니라는 가정 하에 accuracy 사용.
        accuracy = accuracy_score(y_test, y_pred)
        self.stdout.write(f'  ✓ 정확도: {accuracy:.4f} ({accuracy*100:.2f}%)')

        # 교차 검증
        cv_scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=options['cv'],                # fold 수
            scoring='accuracy'               # accuracy로 평가
        )
        self.stdout.write(
            f'  ✓ 교차 검증 평균: {cv_scores.mean():.4f} '
            f'  ✓ 표준편차 : (±{cv_scores.std():.4f})'
        )

        # 분류 리포트
        self.stdout.write('\n  분류 리포트:')

        # output_dict=True로 딕셔너리 형태로 반환받음.-> 필요한 정보만 선별 출력 가능.
        report = classification_report(y_test, y_pred, output_dict=True)

        # 각 라벨별 precision, recall, f1 점수 출력
        for label in ['positive', 'negative']:
            if label in report:
                precision = report[label]['precision']
                recall = report[label]['recall']
                f1 = report[label]['f1-score']
                self.stdout.write(
                    f'    {label:10s} - Precision: {precision:.4f}, '
                    f'Recall: {recall:.4f}, F1: {f1:.4f}'
                )

        # 혼동 행렬
            # labels=['negative','positive']일 때,
            # cm[0][0]=TN, cm[0][1]=FP, cm[1][0]=FN, cm[1][1]=TP 로 읽을 수 있음
        cm = confusion_matrix(y_test, y_pred, labels=['negative', 'positive'])
        self.stdout.write('\n  Confusion Matrix:')
        self.stdout.write(f'    TN: {cm[0][0]:4d}  |  FP: {cm[0][1]:4d}')
        self.stdout.write(f'    FN: {cm[1][0]:4d}  |  TP: {cm[1][1]:4d}')

        # 6. 모델 저장
        self.stdout.write('\n[6/6] 모델 저장')

        # 저장 경로
        base_dir = DEFAULT_MODEL_DIR # 상대경로. # apps/comparisons/ai_models
        base_dir.mkdir(parents=True, exist_ok=True) # 디렉토리 없으면 생성, 상위폴더까지 생성 옵션,

        # 모델 및 메타데이터 경로
        model_path = base_dir / 'sentiment_pipeline.joblib'
        metadata_path = base_dir / 'model_metadata.json'

        # 모델 저장
        # joblib으로 파이프라인 통째로 저장 (tfidf + clf)
        joblib.dump(pipeline, model_path)
        self.stdout.write(f'  ✓ 모델 저장: {model_path}')

        # 메타데이터 저장
        metadata = {
            'version': '1.0.0',                       # 버전(수동 관리)
            'accuracy': float(accuracy),              # 테스트 정확도
            'cv_mean': float(cv_scores.mean()),       # CV 평균
            'cv_std': float(cv_scores.std()),         # CV 표준편차
            'train_size': len(X_train),               # 학습 데이터 크기
            'test_size': len(X_test),                 # 테스트 데이터 크기
            'classes': list(pipeline.classes_),       # 클래스 순서(중요!)
            'hyperparameters': {                      # 학습에 사용한 하이퍼파라미터 기록
                'min_df': options['min_df'],
                'ngram_range': (1, options['ngram']),
                'C': options['C'],
                'max_features': 5000
            },
            'classification_report': report           # 리포트 전체 저장(추후 분석/모니터링용)
        }

        # 메타데이터 JSON으로 저장
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self.stdout.write(f'  ✓ 메타데이터 저장: {metadata_path}')

        # 완료
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('모델 학습 완료!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 테스트 예측 예시
        self.stdout.write('\n테스트 예측 예시:')
        test_samples = [
            '강의가 정말 유익하고 재미있었습니다.',
            '내용이 너무 어렵고 이해가 안 돼요.',
            '교수님 설명이 명확해서 좋았어요.'
        ]

        for sample in test_samples:
            # 단일 샘플 예측 라벨
            pred = pipeline.predict([sample])[0]
            # 단일 샘플 확률 분포
            proba = pipeline.predict_proba([sample])[0]
            # # NOTE 신뢰도 계산 : #우선은 단순하게, 추후 개선 고려.
            confidence = (max(proba) - 0.5) * 2

            self.stdout.write(
                f'  "{sample}"\n'
                f'    → {pred} (신뢰도: {confidence:.2f})\n'
            )