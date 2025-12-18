import pandas as pd

# 1. 컬럼명 직접 정의 (아까 CSV 저장할 때 썼던 순서대로)
column_names = [
    'id', 'shortname', 'name', 'url', 'course_image', 'org', 'org_name',
    'enrollment_start', 'enrollment_end', 'study_start', 'study_end',
    'professor', 'public_yn', 'summary', 'classfy_name', 'middle_classfy_name',
    'week', 'course_playtime', 'detail_error_raw'
]

# 2. CSV 읽기 
# header=None: 첫 줄부터 데이터로 인식 (누락 방지)
# encoding='utf-8-sig': 한글 깨짐 방지
df = pd.read_csv('kmooc_courses_final.csv', names=column_names, header=None, encoding='utf-8-sig')

# 3. 불필요한 열 제거
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# 4. JSON 변환
df.to_json('kmooc_courses.json', orient='records', force_ascii=False, indent=4)