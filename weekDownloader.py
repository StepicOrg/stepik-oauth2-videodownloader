import requests
import json
import urllib
import urllib.request
from settings import client_id, client_secret
from requests.auth import HTTPBasicAuth

def get_course_page(api_url, token):
    return json.loads(requests.get(api_url).text)

def get_all_weeks(stepicResp, token):
    return course_data['courses'][0]['sections']

def get_unit_list(sectionList, token):
    resp = [json.loads(requests.get('https://stepic.org/api/sections/' + str(arr), headers={'Authorization': 'Bearer '+ token}).text) for arr in sectionList]
    return [section['sections'][0]['units'] for section in resp]

def get_steps_list(units_list, week, token):
    data = [json.loads(requests.get('https://stepic.org/api/units/' + str(unit_id), headers={'Authorization': 'Bearer '+ token}).text) for unit_id in units_list[week-1]]
    # pprint.pprint(data)
    lesson_lists = [elem['units'][0]['lesson'] for elem in data]
    data = [json.loads(requests.get('https://stepic.org/api/lessons/' + str(lesson_id), headers={'Authorization': 'Bearer '+ token}).text)['lessons'][0]['steps']
            for lesson_id in lesson_lists]
    steps_list = [item for sublist in data for item in sublist]

    return steps_list


def get_only_video_steps(step_list, token):
    resp_list = list()
    for s in step_list:
        # print(s)
        resp = json.loads(requests.get('https://stepic.org/api/steps/' + str(s), headers={'Authorization': 'Bearer '+ token}).text)
        if resp['steps'][0]['block']['video']:
            resp_list.append(resp['steps'][0]['block'])
    print('Only video:', len(resp_list))
    return resp_list


if __name__ == '__main__':
    s = requests.Session()
    auth = HTTPBasicAuth(client_id, client_secret)
    x = requests.post('https://stepic.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
    token = json.loads(x.text)['access_token']

    course_data = get_course_page('http://stepic.org/api/courses/91', token)
    weeks = get_all_weeks(course_data, token)
    all_units = get_unit_list(weeks, token)
    all_steps = get_steps_list(all_units, 4, token)
    only_video_steps = get_only_video_steps(all_steps, token)
    url_list_with_q = [x['video']['urls'][0] for x in only_video_steps]
    url_list = [x['url'] for x in url_list_with_q]
    for i, el in enumerate(url_list):
        filename = 'Video_'+str(i)+'.mp4'
        print('Downloading file ', filename)
        urllib.request.urlretrieve(el, filename)
        print('Done')
    print("All steps downloaded")