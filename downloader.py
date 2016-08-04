import argparse
import json
import os
import urllib
import urllib.request
import requests
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


def parse_arguments():
    """
    Parse input arguments with help of argparse.
    """

    parser = argparse.ArgumentParser(
        description='Stepic downloader')

    parser.add_argument('-c', '--client_id',
                        help='your client_id from https://stepic.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-s', '--client_secret',
                        help='your client_secret from https://stepic.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-i', '--course_id',
                        help='course id',
                        required=True)

    parser.add_argument('-w', '--week_id',
                        help='week id starts from 1 (if not set then it will download the whole course)',
                        type=int,
                        default=None)

    parser.add_argument('-q', '--quality',
                        help='quality of a video. Default is 720',
                        choices=['360', '720', '1080'],
                        default='720')

    parser.add_argument('-o', '--output_dir',
                        help='output directory. Default is the current dolder',
                        default='.')

    args = parser.parse_args()

    return args


def main():
    args = parse_arguments()

    """
    Example how to receive token from Stepic.org
    Token should also been add to every request header
    example: requests.get(api_url, headers={'Authorization': 'Bearer '+ token})
    """

    auth = HTTPBasicAuth(args.client_id, args.client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
    token = json.loads(resp.text)['access_token']

    course_data = get_course_page('http://stepic.org/api/courses/' + args.course_id, token)

    weeks_num = get_all_weeks(course_data)

    all_units = get_unit_list(weeks_num, token)

    # Loop through all week in a course and
    # download all videos or
    # download only for the week_id is passed as an argument.
    for week in range(len(weeks_num)):
        # Skip if week_id is passed as an argument
        if args.week_id:
            if week != args.week_id:
                continue

        all_steps = get_steps_list(all_units, week, token)

        only_video_steps = get_only_video_steps(all_steps, token)

        url_list_with_q = []

        # Loop through videos and store the url link and the quality.
        for video_step in only_video_steps:
            video_link = None
            msg = None

            # Check a video quality.
            for url in video_step['video']['urls']:
                if url['quality'] == args.quality:
                    video_link = url['url']

            # If the is no required video quality then download
            # with the best available quality.
            if video_link is None:
                msg = "The requested quality = {} is not available!".format(args.quality)

                video_link = video_step['video']['urls'][0]['url']

            # Store link and quality.
            url_list_with_q.append({'url': video_link, 'msg': msg})

        # Compose a folder name.
        folder_name = os.path.join(args.output_dir, args.course_id, 'week_' + str(week))

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

        for week, el in enumerate(url_list_with_q):
            # Print a message if something wrong.
            if el['msg']:
                print("{}".format(el['msg']))

            filename = os.path.join(folder_name, 'Video_' + str(week) + '.mp4')
            print('Downloading file ', filename)
            urllib.request.urlretrieve(el['url'], filename)
            print('Done')
        print("All steps downloaded")


if __name__ == "__main__":
    main()
