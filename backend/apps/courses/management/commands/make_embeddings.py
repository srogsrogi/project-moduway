import os
import requests
import json
import re
from django.core.management.base import BaseCommand
from apps.courses.models import Course

class Command(BaseCommand):
    help = "강의 데이터를 전처리 후 배치 방식으로 임베딩을 생성하여 저장합니다."

    def handle(self, *args, **options):
        # 1. 설정 및 환경 변수
        GMS_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
        GMS_KEY = os.environ.get("GMS_KEY")
        BATCH_SIZE = 2

        if not GMS_KEY:
            self.stdout.write(self.style.ERROR("GMS_KEY가 설정되지 않았습니다."))
            return

        # 2. 임베딩이 필요한 데이터 추출 (embedding이 없는 것만)
        courses = list(Course.objects.filter(embedding__isnull=True))
        total_count = len(courses)

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("임베딩할 새로운 데이터가 없습니다."))
            return

        self.stdout.write(f"총 {total_count}개의 강의 처리를 시작합니다. (Batch Size: {BATCH_SIZE})")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GMS_KEY}"
        }

        # 3. 배치 단위 루프
        for i in range(0, total_count, BATCH_SIZE):
            batch_segment = courses[i : i + BATCH_SIZE]
            processed_texts = []
            valid_courses = []

            for course in batch_segment:
                # --- 전처리 로직 시작 ---
                name = course.name or ""
                summary = course.summary or ""
                category = f"{course.classfy_name or ''} {course.middle_classfy_name or ''}"

                # (1) 불용어 및 노이즈 제거
                text = f"{category} {summary}"
                text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text) # 이메일 제거
                text = re.sub(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', '', text) # 날짜 제거
                
                stopwords = ['주차', '학교', 'email', '이메일', '수강신청', '이수증', '석사', '박사', '저서', 
                             '출판사', '학지사', '퀴즈', '공개', '일시', '주요경력', '전)', '현)', '주제']
                for word in stopwords:
                    text = text.replace(word, '')

                # 특수문자 제거 및 공백 정규화
                text = re.sub(r'[^\w\s가-힣]', ' ', text)
                text = " ".join(text.split())

                # (2) 제목 반복 (Title Boosting) 및 길이 제한
                # 제목 3번 반복
                boosted_name = (name + " ") * 3
                combined_text = f"{boosted_name} {text}".strip()

                # (3) [핵심 안전장치] 개별 텍스트 길이 제한
                # 한글 기준 3,000자면 약 4,500~5,000 토큰입니다. 
                # 배치 2개의 합이 8,192 토큰을 넘지 않도록 안전하게 3,000자로 제한합니다.
                if len(combined_text) > 3000:
                    combined_text = combined_text[:3000]

                if combined_text:
                    processed_texts.append(combined_text)
                    valid_courses.append(course)

            if not processed_texts:
                continue

            # 4. GMS(OpenAI) 배치 호출
            try:
                data = {
                    "model": "text-embedding-3-small",
                    "input": processed_texts
                }
                
                response = requests.post(GMS_URL, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings = result['data']
                    
                    # 5. DB 저장 (배치 성공 시 루프 돌며 저장)
                    for idx, emb_data in enumerate(embeddings):
                        target_course = valid_courses[idx]
                        target_course.embedding = emb_data['embedding']
                        target_course.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"완료: {min(i + BATCH_SIZE, total_count)} / {total_count}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Batch 실패 (Status: {response.status_code}): {response.text}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))

        self.stdout.write(self.style.SUCCESS("모든 작업이 완료되었습니다."))