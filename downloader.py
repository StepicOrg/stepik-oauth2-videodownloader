import getopt
import os
import requests
import json
import urllib
import urllib.request
import sys
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
    """
    Parse input arguments with help of getopt.
    """

    help = 'usage: downloader [-h] ' \
           '--course_id=COURSE_ID ' \
           '--client_id=CLIENT_ID ' \
           '--client_secret=CLIENT_SECRET ' \
           '[--week_id=WEEK_ID] ' \
           '[--quality=360|720|1080] ' \
           '[--output_dir=.]' \
           '\n\nMandatory parameters:\n' \
           '-c, --client_id         your client_id from https://stepic.org/oauth2/applications/\n' \
           '-s, --client_secret     your client_secret from https://stepic.org/oauth2/applications/\n' \
           '-i, --course_id         course id\n' \
           '\nOptional arguments:\n' \
           '-w, --week_id           week id (if not set then download the whole course)\n' \
           '-q, --quality           quality of a video. Default is 720\n' \
           '-o, --output_dir        Output directory. Default is the current dolder\n' \
           '-h, --help              shows help'

    course_id = None
    client_id = None
    client_secret = None
    week_id = None
    quality = 720
    output_dir = '.'

    try:
        opts, args = getopt.getopt(argv, "hc:i:s:q:o:",
                                   ["course_id=",
                                    "client_id=",
                                    "client_secret=",
                                    "week_id=",
                                    "quality=",
                                    "output_dir="])
    except getopt.GetoptError:
        print(help)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help)
            sys.exit()
        elif opt in ('-c', '--course_id'):
            course_id = arg
        elif opt in ('-i', '--client_id'):
            client_id = arg
        elif opt in ('-s', '--client_secret'):
            client_secret = arg
        elif opt in ('-w', '--week_id'):
            week_id = int(arg)
        elif opt in ('-q', '--quality'):
            quality = arg
        elif opt in ('-o', '--output_dir'):
            output_dir = arg

    check_argument(course_id, "course_id is wrong!", help)
    check_argument(client_id, "client_id is wrong!", help)
    check_argument(client_secret, "client_secret is wrong!", help)

    """
    Example how to receive token from Stepic.org
    Token should also been add to every request header
    example: requests.get(api_url, headers={'Authorization': 'Bearer '+ token})
    """

    auth = HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
    token = json.loads(resp.text)['access_token']

    course_data = get_course_page('http://stepic.org/api/courses/' + course_id, token)

    weeks_num = get_all_weeks(course_data)

    all_units = get_unit_list(weeks_num, token)

    # Loop through all week in a course and
    # download all videos or
    # download only for the week_id is passed as an argument.
    for week in range(len(weeks_num)):
        # Skip if week_id is passed as an argument
        if week_id:
            if week != week_id:
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
                if url['quality'] == quality:
                    video_link = url['url']

            # If the is no required video quality then download
            # with the best available quality.
            if video_link is None:
                msg = "The requested quality = {} is not available!".format(quality)

                video_link = video_step['video']['urls'][0]['url']

            # Store link and quality.
            url_list_with_q.append({'url': video_link, 'msg': msg})

        # Compose a folder name.
        folder_name = os.path.join(output_dir, course_id, 'week_' + str(week))

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


def check_argument(parameter, msg, help_msg):
    """
    Check passing argument and if it is None
    then print a message and a help message.

    :param parameter: any variable
    :param msg: message
    :param help_msg: help message
    :return: None
    """
    if parameter is None:
        print(msg)
        print()
        print(help_msg)
        sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
