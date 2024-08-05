from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

def scrape_data(url,file_year,file_major):
    # 브라우저를 헤드리스 모드로 설정
    options = Options()
    options.headless = True

    # WebDriver 설정
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 웹페이지 접근
    driver.get(url)

    # 데이터를 담을 리스트 초기화
    data = []

    # 테이블 찾기
    try:
        # 테이블을 포함하는 div 요소를 찾기
        table_div = driver.find_element(By.XPATH, '//*[@id="contents"]/div[3]/div[2]')
        table = table_div.find_element(By.XPATH, './/table')

        # 테이블의 행들 추출
        rows = table.find_elements(By.XPATH, './/tr')
        for row in rows:
            cells = row.find_elements(By.XPATH, './/th|.//td')
            row_data = [cell.text.strip() for cell in cells]
            if "소계" not in row_data:  # "소계"가 포함된 행 제거
                data.append(row_data)

        # 첫 번째 행을 컬럼 헤더로 설정
        columns = data[0]
        data = data[1:]

        # 데이터를 DataFrame으로 변환
        df = pd.DataFrame(data, columns=columns)

        # 최대 컬럼 수 결정
        max_columns = max(len(row) for row in data)

        # 빈 셀을 채우기
        new_data = []
        for row in data:
            new_row = ["" for _ in range(max_columns - len(row))] + row
            new_data.append(new_row)

        # 새로운 데이터를 DataFrame으로 변환
        df = pd.DataFrame(new_data, columns=columns)
        
        # 빈 셀을 바로 위의 값으로 채우기
        for col in df.columns:
            df[col] = df[col].replace('', pd.NA).fillna(method='ffill')

        # "학점(설계)" 컬럼을 "학점"과 "설계"로 나누기
        if '학점(설계)' in df.columns:
            # 결합된 컬럼을 두 개의 개별 컬럼으로 나누기
            df[['학점', '설계']] = df['학점(설계)'].str.extract(r'(\d+)\((\d+)\)', expand=True)
            # 괄호 안에 값이 없는 경우 처리
            df['학점'] = df['학점'].fillna(df['학점(설계)'].str.extract(r'(\d+)')[0])
            df['설계'] = df['설계'].fillna(0).astype(int)
            # 원래 결합된 컬럼 제거
            df = df.drop(columns=['학점(설계)'])
            
            df = df.rename(columns={'학점': '학점(설계)'})

        # "년도" 컬럼 추가
        year_div = driver.find_element(By.XPATH, '//*[@id="contents"]/div[3]/div[1]')
        year = year_div.text.strip()[2:4] if year_div else 'Unknown Year'

        # "학과" 컬럼 추가
        dept_link = driver.find_element(By.XPATH, '/html/body/div/div[3]/div/ul/li[3]/a/span')
        department = (dept_link.text.strip() + '과') if dept_link else 'Unknown Department'

        # '년도'와 '학과' 컬럼 추가
        df.insert(0, '년도', year)
        df.insert(2, '학과', department)

        # DataFrame을 CSV 파일로 저장 (인덱스 없이)
        file_path = "gonghak_crawl\\gonghak_result_archive\\"
        result_file_name = file_path + str(file_year)+"_"+str(file_major)+"_"+'course_requirements_normalized_case1.csv'
        df.to_csv(result_file_name, index=False)

        print("Data has been saved to ", result_file_name)

    finally:
        driver.quit()

def work_list_data() :
    work_list = pd.read_csv('gonghak_crawl\\work_list.csv')
    return work_list
    
if __name__ == "__main__":
    # scrape_data("https://abeek.sejong.ac.kr/abeek/program0302_6.html","연습","major")
    for index, row in work_list_data().iterrows():
        year = row['년도']
        major = row['학과']
        link = row['링크']
        try:
            scrape_data(link, year, major)
        except Exception as e:
            # 에러가 발생하면 pass하여 다음 연산을 계속
            print("에러 파일 : ",link," ",year," ",major)
            # print(f"Error occurred with link {link}, year {year}, major {major}: {e}")
            pass
