from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import re
import csv

def scrape_data(url):
    # 브라우저를 헤드리스 모드로 설정
    options = Options()
    options.headless = True

    # WebDriver 설정
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 웹페이지 접근
    driver.get(url)

    # 지정된 XPath에서 텍스트를 추출하여 년도 정보 추출
    year_div = driver.find_element(By.XPATH, '//*[@id="contents"]/div[3]/div[1]')
    year_text = year_div.text.strip()

    # 뒤의 두 자리 숫자만 추출
    last_two_digits = re.findall(r'\d{2}', year_text)
    last_two_digits = last_two_digits[-1] if last_two_digits else ""

    # "학과" 정보 추출
    dept_link = driver.find_element(By.XPATH, '/html/body/div/div[3]/div/ul/li[3]/a/span')
    department = (dept_link.text.strip() + '과') if dept_link else 'Unknown Department'

    # 주어진 XPath를 사용하여 테이블 찾기
    table = driver.find_element(By.XPATH, '//*[@id="contents"]/div[3]/div[2]/table')

    # 테이블 데이터를 저장할 리스트 초기화
    data = []
    current_grade = ""  # 현재 학년을 저장할 변수

    # 테이블의 행을 반복 처리
    rows = table.find_elements(By.XPATH, './/tr')
    for row in rows:
        # 헤더 또는 소계 행을 건너뜀
        if row.find_elements(By.XPATH, './/th') or "소계" in row.text:
            grade_cell = row.find_elements(By.XPATH, './/td[@class="cell_0" and @rowspan]')
            if grade_cell and int(grade_cell[0].get_attribute("rowspan")) >= 3:
                current_grade = grade_cell[0].find_element(By.XPATH, './/span').text.strip() if grade_cell[0].find_elements(By.XPATH, './/span') else "알 수 없음"
            continue

        grade_cell = row.find_elements(By.XPATH, './/td[@class="cell_0" and @rowspan]')
        if grade_cell and int(grade_cell[0].get_attribute("rowspan")) >= 3:
            current_grade = grade_cell[0].find_element(By.XPATH, './/span').text.strip() if grade_cell[0].find_elements(By.XPATH, './/span') else "알 수 없음"

        # 데이터 행을 처리
        cells = row.find_elements(By.XPATH, './/td')
        row_data = []
        for cell in cells:
            # 셀의 텍스트를 직접 가져오기
            text = cell.text.strip()
            cleaned_text = re.sub(' +', ' ', text)
            cleaned_text = re.sub('\n','', cleaned_text)
            row_data.append(cleaned_text)
        
        # 정확히 6개의 요소가 있는 행만 추가 (1학기/2학기 구조에 맞게)
        if len(row_data) == 6:
            semester_data = {
                "학년": current_grade,
                "1학기": {
                    "이수구분": row_data[0],
                    "과목명": row_data[1],
                    "학점(설계)": row_data[2],
                },
                "2학기": {
                    "이수구분": row_data[3],
                    "과목명": row_data[4],
                    "학점(설계)": row_data[5],
                }
            }
            data.append(semester_data)

    # "년도"와 "학과" 정보를 포함하는 JSON 데이터 구조 생성
    output_data = {
        "년도": last_two_digits,
        "학과": department,
        "데이터": data
    }

    # JSON 형식으로 변환하여 출력
    json_output = json.dumps(output_data, ensure_ascii=False, indent=4)

    # 선택적으로 JSON을 파일로 저장
    with open('gonghak_crawl\\output_case2.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json_output)

    print("JSON 데이터가 생성되어 'output_case2.json' 파일로 저장되었습니다.")

    # 브라우저 종료
    driver.quit()


def process_json_to_csv(file_year, file_major):
    def normalize_string(s):
        return re.sub(r'\s+', '', s)

    # JSON 데이터를 읽어오기
    with open('gonghak_crawl\\output_case2.json', 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    # 기존 CSV 파일 데이터 읽기
    csv_file_path = 'gonghak_crawl\\courses_case2.csv'
    course_data = []
    with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            course_data.append(row)

    # 새로운 CSV 파일을 생성
    
    output_file_path = 'gonghak_crawl\\gonghak_result_archive\\'+str(file_year)+'_'+str(file_major)+'_course_requirements_normalized_case2.csv'
    with open(output_file_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
        fieldnames = ['년도', '학년', '학과', '학기', '교과구분', '인증구분', '교과목명', '학점(설계)', '설계']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # 헤더 작성
        writer.writeheader()

        # JSON 데이터에서 필요한 정보를 추출하여 작성
        for entry in json_data["데이터"]:
            for semester, details in entry.items():
                if semester in ['1학기', '2학기']:
                    course_name = details["과목명"]
                    
                    # print(course_name)
                    
                    if course_name == "":
                        continue
                    
                    # 기존 CSV 파일에서 해당 과목의 교과구분을 찾기 (공백 제거하여 비교)
                    matching_course = next(
                        (course for course in course_data if normalize_string(course['강의명']) == normalize_string(course_name)), 
                        "전공"
                    )
                     # 학점(설계) 처리
                    학점설계 = details["학점(설계)"]
                    if '(' in 학점설계 and ')' in 학점설계:  # 예: "3(1)"
                        학점, 설계 = 학점설계.split('(')
                        설계 = 설계.replace(')', '')
                    else:
                        학점 = 학점설계
                        설계 = '0'
                    
                    writer.writerow({
                        '년도': json_data['년도'],
                        '학년': entry['학년'],
                        '학과': json_data['학과'],
                        '학기': '1' if semester == '1학기' else '2',
                        '교과구분': "전공",
                        '인증구분': details["이수구분"],
                        '교과목명': course_name,
                        '학점(설계)': 학점,
                        '설계': 설계
                    })

    print(f"CSV 파일이 '{output_file_path}'로 생성되었습니다.")

def work_list_data() :
    work_list = pd.read_csv('gonghak_crawl\\work_list.csv')
    return work_list

if __name__ == "__main__":
    
    for index, row in work_list_data().iterrows():
        year = row['년도']
        major = row['학과']
        link = row['링크']
        if(major=="데사" or (major=="컴공" and str(year)=="2017")):
            try:
                scrape_data(link)
                process_json_to_csv(year,major)
            except Exception as e:
                # 에러가 발생하면 pass하여 다음 연산을 계속
                print("에러 파일 : ",link," ",year," ",major)
                # print(f"Error occurred with link {link}, year {year}, major {major}: {e}")
                pass
