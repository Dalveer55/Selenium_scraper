from bs4 import BeautifulSoup
import requests
import pandas as pd
import hashlib
from concurrent.futures import ThreadPoolExecutor
def step_two(x):
    page_data = {
        'url': x
    }
    req2 = requests.get(x)
    soup2 = BeautifulSoup(req2.content ,"lxml")
    for raw1 in soup2.find_all('div', class_='project-details')[0::3]:
        try:
            heading1 = raw1.find('h2', class_='scope-heading').text.strip()
        except:
            heading1 = ''
        try:    
            value1 = raw1.find('div', class_='text-block-31').text.strip()
        except:
            value1 = ''
        page_data[heading1] = value1

    for raw2 in soup2.find_all('div', class_='project-details')[1::3]:
        try:
            heading2 = raw2.find('h3', class_='details-heading').text.strip()
        except:
            heading2 = ''
        try:
            value2 = raw2.find('div', class_='paid').text.strip()
        except:
            value2 = ''
        page_data[heading2] = value2

    for raw3 in soup2.find_all('div', class_='project-details')[2::3]:
        for raw3_all in raw3.find_all('div', class_='project-specs'):
            try:
                heading3 = raw3_all.find('h3', class_='details-heading').text.strip().lower()
            except:
                heading3 = ''
            try:
                value3 = raw3_all.find('div', class_='date-wrapper').text.strip()
            except:
                value3 = ''
            page_data[heading3] = value3
    try:
        disclamer = soup2.find('div', class_='disclaimer').text.strip()
    except:
        disclamer = ''     
    page_data['disclaimer'] = disclamer
    
    try: 
        for id in soup2.find('div', id='projectID'):
            original_id = id.text.strip() 
    except:
        original_id = ''
    page_data['original_id'] = original_id
    return page_data



url_x = 'https://atldot.atlantaga.gov/projects'
req = requests.get(url_x, verify=False)
soup = BeautifulSoup(req.content ,"lxml")
me = soup.find('table', id='projects').tbody

all_tables = pd.read_html(req.text)
all_tables = pd.DataFrame(all_tables[0])

url_list = []
page_data = {}
for title_raw in me.find_all('a', class_='title-link w-inline-block'):
    title = 'https://atldot.atlantaga.gov' + title_raw.get('href')
    url_list.append(title)

df = pd.DataFrame(list(zip(url_list, all_tables['Name'].tolist())),
    columns=['url','Name']
)  
df2 = all_tables.merge(df, on='Name', how='inner')

with ThreadPoolExecutor(max_workers=10) as exe:
    results2 = list(exe.map(step_two, df2['url'].tolist()))

df3 = pd.DataFrame(results2)
final_df = df2.merge(df3, on='url', how='inner')

final_df.rename(columns={ 
    'project start': 'project_start_date',
    'Name': 'title',
    'Type': 'project_type',
    'Phase': 'status',
    'Paid': 'paid',
    'Scope': 'description',
    'Council District': 'council_district',
    }, inplace=True)

final_df['id'] = final_df['url'].apply(
    lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest()
)
final_df['id'] = 'ATLANTA_usa' + '_' + final_df['id']

final_df['project_start_date'] = pd.to_datetime(final_df['project_start_date'], errors='coerce').dt.date
final_df['currency'] = final_df['budget'].fillna('').apply(lambda x: 'USD' if str(x) != '' else '')
final_df['city_name'] = 'Atlanta'
final_df['country_name'] = 'United States of America'
final_df.to_csv('altanta_cleaned.csv')
