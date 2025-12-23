# EDA 이후 발견한 특성에 따라 classfy_name 결측치 기준으로 2개 데이터를 삭제했기 때문에 전처리 자동화시 해당 사항 고려하여 코드 수정 필요

import pandas as pd
import os
import numpy as np

# --- 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "raw_data", "kmooc_courses_final.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "cleaned_data")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "kmooc_courses_public.csv")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "kmooc_courses_public.json")

COLUMN_NAMES = [
    'id', 'shortname', 'name', 'url', 'course_image', 'org', 'org_name',
    'enrollment_start', 'enrollment_end', 'study_start', 'study_end',
    'professor', 'public_yn', 'summary', 'raw_summary', 'classfy_name', 'middle_classfy_name',
    'week', 'course_playtime', 'detail_error_raw'
]

def filter_and_save():
    print("🚀 데이터 로드 중...")
    
    try:
        df = pd.read_csv(INPUT_CSV, names=COLUMN_NAMES, header=None, encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return

    print(f"📊 원본 데이터: {len(df)}건")

    # --- 1. 기본 필터링: public_yn != 'N' ---
    if 'public_yn' in df.columns:
        df['public_yn'] = df['public_yn'].astype(str).str.strip()
        df = df[df['public_yn'] != 'N']
    else:
        print("❌ 'public_yn' 컬럼을 찾을 수 없습니다.")
        return

    # --- 2. 추가 필터링: classfy_name 결측치 제거 ---
    # 결측치(NaN) 및 공백만 있는 데이터 제거
    initial_count = len(df)
    df = df[df['classfy_name'].notnull()]
    df = df[df['classfy_name'].astype(str).str.strip() != ""]
    print(f"🧹 classfy_name 결측치 제거 완료 (제거건수: {initial_count - len(df)}건)")

    # --- 3. 추가 필터링: course_playtime > 0 ---
    # 수치형으로 변환 후 0보다 큰 데이터만 유지
    initial_count = len(df)
    df['course_playtime'] = pd.to_numeric(df['course_playtime'], errors='coerce')
    df = df[df['course_playtime'] > 0]
    print(f"🧹 course_playtime 0 이하 데이터 제거 완료 (제거건수: {initial_count - len(df)}건)")

    print(f"✅ 최종 필터링 후 데이터: {len(df)}건")

    # 3. 저장
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # CSV 저장
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"💾 CSV 저장 완료: {OUTPUT_CSV}")

    # JSON 저장
    df.to_json(OUTPUT_JSON, orient='records', force_ascii=False, indent=4)
    print(f"💾 JSON 저장 완료: {OUTPUT_JSON}")

if __name__ == "__main__":
    filter_and_save()