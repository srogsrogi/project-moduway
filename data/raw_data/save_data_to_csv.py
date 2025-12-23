import requests
import pandas as pd
import time
import os
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import unquote

# --- 설정 ---
SERVICE_KEY = 
BASE_URL = "http://apis.data.go.kr/B552881/kmooc_v2_0"
LIST_URL = f"{BASE_URL}/courseList_v2_0"
DETAIL_URL = f"{BASE_URL}/courseDetail_v2_0"

# 스크립트 위치 기준 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILENAME = os.path.join(BASE_DIR, "kmooc_courses_final.csv")

def clean_html(raw_html):
    """HTML 태그를 제거하고 순수 텍스트만 추출"""
    if not raw_html or not isinstance(raw_html, str):
        return raw_html
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=' ', strip=True)
    except:
        return raw_html

def convert_date(ts):
    """숫자 타임스탬프를 YYYY-MM-DD 형식의 문자열로 변환"""
    if not ts:
        return ts
    try:
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

    fieldnames = [
        'id', 'shortname', 'name', 'url', 'course_image', 'org', 'org_name',
        'enrollment_start', 'enrollment_end', 'study_start', 'study_end',
        'professor', 'public_yn', 'summary', 'raw_summary', 'classfy_name', 'middle_classfy_name',
        'week', 'course_playtime', 'detail_error_raw'
    ]

    with open(SAVE_FILENAME, 'a', newline='', encoding='utf-8-sig') as f:
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
        # 파라미터 대소문자 및 키 적용
        params = {
            'ServiceKey': SERVICE_KEY, 
            'Page': page, 
            'Size': 100
        }
        
        try:
            res = requests.get(LIST_URL, params=params, timeout=15)
            
            # 첫 페이지 호출 시 응답 상태 확인용 디버깅
            if page == 1:
                if res.status_code != 200:
                    print(f"❌ API 연결 실패 (Status: {res.status_code})")
                    print(f"응답 내용: {res.text}")
                    return
            
            data = get_safe_json(res)
            # K-MOOC API는 버전에 따라 items 또는 results에 데이터를 담습니다.
            items = data.get('items') or data.get('results') or []
            
            if not items:
                print(f"ℹ️ {page}페이지에서 수집을 종료합니다. (데이터 없음)")
                break
            
            all_courses.extend(items)
            
            # totalCount 추출 (경로가 유동적일 수 있어 안전하게 추출)
            header = data.get('header') or data.get('meta') or {}
            total = header.get('totalCount') or header.get('count') or len(all_courses)
            
            print(f"✅ 목록 로드 중: {len(all_courses)} / {total}")
            
            if len(all_courses) >= int(total):
                break
                
            page += 1
            time.sleep(0.2) # 서버 부하 방지
            
        except Exception as e:
            print(f"⚠️ 목록 오류: {e}")
            break

    # 2. 상세 정보 보완 및 정제 저장
    if not all_courses:
        print("❌ 수집된 목록이 없어 종료합니다. 서비스키 활성화 여부를 확인하세요.")
        return

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
            detail = detail_data.get('results') or detail_data.get('items') or {}
            
            # 리스트로 오는 경우 첫 번째 요소 선택
            if isinstance(detail, list) and len(detail) > 0:
                detail = detail[0]

            combined = item.copy()
            
            if isinstance(detail, dict):
                combined.update(detail)
                combined['raw_summary'] = combined.get('summary', '')
                combined['summary'] = clean_html(combined.get('summary', ''))
            else:
                combined['detail_error_raw'] = str(detail)
            
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

    print(f"\n✨ 수집 완료! 파일명: {SAVE_FILENAME}")

if __name__ == "__main__":
    main()
