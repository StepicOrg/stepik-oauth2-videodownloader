import os
import requests
import json
import urllib
import urllib.request
import sys
from settings import client_id, client_secret
from requests.auth import HTTPBasicAuth


def get_course_page(api_url, token):
    return json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text)


def get_all_weeks(stepic_resp):
    return stepic_resp['courses'][0]['sections']


def get_unit_list(section_list, token):
    resp = [json.loads(requests.get('https://stepic.org/api/sections/' + str(arr),
                                    headers={'Authorization': 'Bearer ' + token}).text)
            for arr in section_list]
    return [section['sections'][0]['units'] for section in resp]


def get_steps_list(units_list, week, token):
    data = [json.loads(requests.get('https://stepic.org/api/units/' + str(unit_id),
                                    headers={'Authorization': 'Bearer ' + token}).text)
            for unit_id in units_list[week - 1]]
    lesson_lists = [elem['units'][0]['lesson'] for elem in data]
    data = [json.loads(requests.get('https://stepic.org/api/lessons/' + str(lesson_id),
                                    headers={'Authorization': 'Bearer ' + token}).text)['lessons'][0]['steps']
            for lesson_id in lesson_lists]
    return [item for sublist in data for item in sublist]


def get_only_video_steps(step_list, token):
    resp_list = list()
    for s in step_list:
        resp = json.loads(requests.get('https://stepic.org/api/steps/' + str(s),
                                       headers={'Authorization': 'Bearer ' + token}).text)
        if resp['steps'][0]['block']['video']:
            resp_list.append(resp['steps'][0]['block'])
    print('Only video:', len(resp_list))
    return resp_list


def main(argv):
    if len(argv) != 4:
        print('Input Error, pass 4 arguments: \nfirst - Course_id, '
              'second - Week index, third - folder name, forth - quality.'
              '\nExample: python weekDownloader.py "154" "1" "." "720" ')
        sys.exit('1')

    """
    Example how to receive token from Stepic.org
    Token should also been add to every request header
    example: requests.get(api_url, headers={'Authorization': 'Bearer '+ token})
    """

    auth = HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
    token = json.loads(resp.text)['access_token']

    course_data = get_course_page('http://stepic.org/api/courses/' + argv[0], token)
    all_units = get_unit_list(get_all_weeks(course_data), token)
    all_steps = get_steps_list(all_units, int(argv[1]), token)
    only_video_steps = get_only_video_steps(all_steps, token)

    url_list_with_q = []

    for video_step in only_video_steps:
        video_link = None

        # Check a video quality.
        for url in video_step['video']['urls']:
            if url['quality'] == argv[3]:
                video_link = url

        # If the is no required video quality then download
        # with the best available quality.
        if video_link is None:
            print("The requested quality = {} is not available!".format(argv[2]))

            video_link = video_step['video']['urls'][0]

        url_list_with_q.append(video_link)

    url_list = [x['url'] for x in url_list_with_q]

    folder_name = argv[2]

    # Create a folder if needed.
    if not os.path.isdir(folder_name):
        try:
            # Create a directory for a particular week in the course.
            os.makedirs(folder_name)
        except PermissionError:
            print("Run the script from admin")
            exit(1)
        except FileExistsError:
            print("Please delete the folder " + folder_name)
            exit(1)

    print('Folder_name ', folder_name)

    for i, el in enumerate(url_list):
        filename = folder_name + '/' + 'Video_' + str(i) + '.mp4'
        print('Downloading file ', filename)
        urllib.request.urlretrieve(el, filename)
        print('Done')
    print("All steps downloaded")


if __name__ == "__main__":
    main(sys.argv[1:])
