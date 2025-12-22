# backend/apps/comparisons/management/commands/generate_dummy_reviews.py

import csv
import random
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    [설계 의도]
    - 감성분석 모델 학습을 위한 초기 학습 데이터가 없거나 부족한 상황에서
      빠르게 테스트/개발용 학습 데이터를 생성하기 위함
    - 실제 "강의 도메인"의 사용자 리뷰와 유사한 문장 구조를 갖는
      '긍정/부정' 이진 분류 데이터셋을 자동 생성

    [상세 고려사항]
    - Django management command 형태로 구현하여
      개발/운영 환경 어디서든 `manage.py` 명령으로 손쉽게 실행 가능
    - 생성되는 데이터는 CSV 형식으로 저장하여
      pandas, sklearn 등 다양한 ML 파이프라인과 즉시 연동 가능
    - 긍정/부정 데이터를 1:1 비율로 생성하여
      학습 시 클래스 불균형으로 인한 편향을 최소화
    -> 실제 서비스에서는 사용자 리뷰 분포가 다를 수 있으므로
       추후 실제 데이터를 반영한 재학습이 필요함
    -> # NOTE 현재는 긍정/부정 데이터를 1:1 비율로 생성했다는 가정 하에, 
       train_model.py에서 CV를 진행함에 있어 Accuracy 지표를 사용함.
    """
    help = '감성분석 학습용 더미 데이터 생성'

    def add_arguments(self, parser):
        """
        커맨드라인 인자 추가
        [인자]
        --count : 생성할 데이터 개수 (기본값: 300)
        --output : 출력 파일 경로 (기본값: fixtures/sentiment_training_data.csv)
        """
        DEFAULT_OUTPUT_PATH = Path(settings.BASE_DIR) / "apps" / "comparisons" / "fixtures" / "sentiment_training_data.csv"
        
        parser.add_argument(
            '--count',
            type=int,
            default=300,
            help='생성할 데이터 개수'
        )

        parser.add_argument(
            '--output',
            type=str,
            default=str(DEFAULT_OUTPUT_PATH),
            help='출력 파일 경로'
        )

    def handle(self, *args, **options):
        """
        [설계 의도]
        - 긍정/부정 리뷰 템플릿을 기반으로
          감성분석 학습에 사용할 CSV 데이터셋을 생성

        [상세 고려사항]
        - 생성된 데이터는 content(텍스트), label(정답) 구조를 따름
        - 랜덤 셔플을 통해 라벨 순서 편향 방지
        - CSV 저장 시 한글 인코딩(utf-8) 명시
        """
        # 생성할 데이터 개수
        count = options['count']
        # 출력 파일 경로
        output_path = Path(options['output'])

        # 출력 디렉토리 생성, 부모 폴더까지 생성 옵션
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f'더미 데이터 {count}개 생성 중...')

        # 긍정 리뷰 템플릿
        positive_templates = [
            "강의 내용이 정말 유익하고 실무에 도움이 됩니다.",
            "교수님 설명이 명확하고 이해하기 쉬워요.",
            "프로젝트 중심으로 배워서 실력이 늘었어요.",
            "과제가 적당하고 복습하기 좋았습니다.",
            "강좌 구성이 체계적이고 좋았어요.",
            "실습 자료가 풍부해서 따라하기 좋았습니다.",
            "강의 퀄리티가 높고 만족스러워요.",
            "초보자도 쉽게 따라갈 수 있어요.",
            "동영상 화질도 좋고 음질도 깨끗합니다.",
            "커리큘럼이 잘 짜여져 있어요.",
            "예제가 실용적이고 이해하기 쉬웠어요.",
            "강사님이 친절하게 질문에 답변해주셨어요.",
            "수료증도 받을 수 있어서 좋았습니다.",
            "비전공자도 충분히 이해할 수 있어요.",
            "가격 대비 정말 만족스러운 강의입니다.",
            "최신 트렌드를 잘 반영한 커리큘럼이에요.",
            "실무 경험이 풍부한 강사님의 노하우가 담겨있어요.",
            "강의 진도가 적절하고 부담스럽지 않아요.",
            "보충 자료도 많이 제공해주셔서 좋았어요.",
            "이 강의 덕분에 취업에 성공했어요!",
        ]

        # 부정 리뷰 템플릿
        negative_templates = [
            "강의 내용이 너무 어렵고 따라가기 힘들어요.",
            "설명이 불친절하고 이해가 잘 안 됩니다.",
            "과제가 너무 많아서 부담스러워요.",
            "동영상 화질이 나빠서 집중하기 어려워요.",
            "커리큘럼이 체계적이지 않아요.",
            "실습 자료가 부족하고 예제가 오래됐어요.",
            "강의 내용이 기대와 달라서 실망했어요.",
            "초보자에게는 너무 어려운 강의입니다.",
            "강사님의 발음이 불명확해서 듣기 힘들어요.",
            "가격 대비 내용이 부실한 것 같아요.",
            "질문 게시판 답변이 느려요.",
            "강의 업데이트가 안 돼서 최신 내용이 없어요.",
            "수강 기간이 너무 짧아요.",
            "강의 속도가 너무 빨라서 따라가기 힘들어요.",
            "이론만 다루고 실습이 부족해요.",
            "내용이 중복되고 지루합니다.",
            "강의 자료 다운로드가 안 돼요.",
            "환불 정책이 불친절해요.",
            "기대했던 것보다 수준이 낮아요.",
            "강의 시간이 너무 길어서 지루해요.",
        ]

        # 데이터 생성
        data = []

        # 긍정 리뷰 생성
        positive_count = count // 2
        for _ in range(positive_count):
            review = random.choice(positive_templates)

            # 문장 다양성 확보를 위한 접두어 랜덤 추가
            if random.random() > 0.5:
                prefix = random.choice([
                    "정말 ", "매우 ", "너무 ", "진짜 ", "아주 ", ""
                ])
                review = prefix + review

            data.append({
                'content': review,
                'label': 'positive'
            })

        # 부정 리뷰 생성
        negative_count = count - positive_count
        for _ in range(negative_count):
            review = random.choice(negative_templates)

            if random.random() > 0.5:
                prefix = random.choice([
                    "정말 ", "너무 ", "진짜 ", "아주 ", ""
                ])
                review = prefix + review

            data.append({
                'content': review,
                'label': 'negative'
            })

        # 셔플
        random.shuffle(data)

        # CSV 저장
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['content', 'label'])
            writer.writeheader()
            writer.writerows(data)

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ {count}개 더미 데이터 생성 완료: {output_path}'
            )
        )

        # 통계 출력
        positive = sum(1 for d in data if d['label'] == 'positive')
        negative = sum(1 for d in data if d['label'] == 'negative')

        self.stdout.write(f'  - 긍정: {positive}개')
        self.stdout.write(f'  - 부정: {negative}개')