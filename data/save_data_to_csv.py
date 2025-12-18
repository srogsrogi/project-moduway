import requests
import pandas as pd
import time
import os
import csv
from bs4 import BeautifulSoup
from datetime import datetime

# --- 설정 ---
SERVICE_KEY = 
BASE_URL = "http://apis.data.go.kr/B552881/kmooc_v2_0"
LIST_URL = f"{BASE_URL}/courseList_v2_0"
DETAIL_URL = f"{BASE_URL}/courseDetail_v2_0"
SAVE_FILENAME = "kmooc_courses_final.csv"

def clean_html(raw_html):
    """HTML 태그를 제거하고 순수 텍스트만 추출"""
    if not raw_html or not isinstance(raw_html, str):
        return raw_html
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        # 태그 사이 공백을 주어 단어가 붙지 않게 처리
        return soup.get_text(separator=' ', strip=True)
    except:
        return raw_html

def convert_date(ts):
    """숫자 타임스탬프를 YYYY-MM-DD 형식의 문자열로 변환"""
    if not ts:
        return ts
    try:
        # 숫자로만 이루어진 문자열이나 숫자형인 경우 변환
        ts_str = str(ts)
        if ts_str.isdigit():
            return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except:
        pass
    return ts

def get_safe_json(response):
    """응답이 유효한 JSON인지 확인하고 딕셔너리로 반환"""
    try:
        return response.json()
    except (ValueError, AttributeError):
        return {"error_fallback": response.text}

def save_to_csv(item_dict):
    """데이터 필드를 고정하여 한 건씩 안전하게 저장"""
    file_exists = os.path.isfile(SAVE_FILENAME)
    if not isinstance(item_dict, dict):
        return

    # 저장할 핵심 필드 순서 정의 (ERD와 매칭하기 편하도록 고정)
    fieldnames = [
        'id', 'shortname', 'name', 'url', 'course_image', 'org', 'org_name',
        'enrollment_start', 'enrollment_end', 'study_start', 'study_end',
        'professor', 'public_yn', 'summary', 'classfy_name', 'middle_classfy_name',
        'week', 'course_playtime', 'detail_error_raw'
    ]

    with open(SAVE_FILENAME, 'a', newline='', encoding='utf-8-sig') as f:
        # fieldnames에 없는 키는 무시하고 저장 (extrasaction='ignore')
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        writer.writerow(item_dict)

def main():
    # 1. 목록 수집 단계
    print("🚀 1단계: 강좌 목록 수집 시작...")
    all_courses = []
    page = 1
    while True:
        params = {'ServiceKey': SERVICE_KEY, 'Page': page, 'Size': 100}
        try:
            res = requests.get(LIST_URL, params=params, timeout=15)
            data = get_safe_json(res)
            items = data.get('items', [])
            if not items: break
            
            all_courses.extend(items)
            total = data.get('header', {}).get('totalCount', 0)
            print(f"✅ 목록 로드 중: {len(all_courses)} / {total}")
            if len(all_courses) >= int(total): break
            page += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ 목록 오류: {e}")
            time.sleep(1); continue

    # 2. 상세 정보 보완 및 정제 저장
    print(f"\n🚀 2단계: {len(all_courses)}건 상세 정보 정제 및 저장 시작...")
    
    processed_ids = set()
    if os.path.isfile(SAVE_FILENAME):
        try:
            df_check = pd.read_csv(SAVE_FILENAME, usecols=['id'])
            processed_ids = set(df_check['id'].astype(str).unique())
            print(f"ℹ️ 기존 파일에서 {len(processed_ids)}건 발견. 이어서 시작합니다.")
        except: pass

    for idx, item in enumerate(all_courses):
        course_id = str(item.get('id'))
        if course_id in processed_ids: continue

        try:
            res_detail = requests.get(DETAIL_URL, params={'ServiceKey': SERVICE_KEY, 'CourseId': course_id}, timeout=15)
            detail_data = get_safe_json(res_detail)
            detail = detail_data.get('results', {})
            
            combined = item.copy()
            
            # 데이터 정제 적용
            if isinstance(detail, dict):
                combined.update(detail)
                # HTML 제거
                combined['summary'] = clean_html(combined.get('summary', ''))
            else:
                combined['detail_error_raw'] = str(detail)
            
            # 날짜 형식 변환 (모든 날짜 필드 대상)
            for date_key in ['enrollment_start', 'enrollment_end', 'study_start', 'study_end']:
                combined[date_key] = convert_date(combined.get(date_key))
            
            save_to_csv(combined)
            
            if (idx + 1) % 50 == 0:
                print(f"💾 진행 상황: {idx + 1} / {len(all_courses)}")
            time.sleep(0.1)
            
        except Exception as e:
            print(f"⚠️ 상세 실패 (ID: {course_id}): {e}")
            save_to_csv(item)
            continue

    print(f"\n수집 완료! 파일명: {SAVE_FILENAME}")

if __name__ == "__main__":
    main()