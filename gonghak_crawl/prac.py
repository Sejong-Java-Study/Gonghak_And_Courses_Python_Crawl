import pandas as pd

if __name__ == "__main__":
    work_list = pd.read_csv('gonghak_crawl\\work_list.csv')
    for index, row in work_list.iterrows():
        year = row['년도']
        major = row['학과']
        link = row['링크']
        print(year, major, link)