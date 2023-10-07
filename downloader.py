import argparse
import json
import os
import urllib
import urllib.request
import urllib.error
from dataclasses import dataclass

import requests
import sys
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional

ID = int  # for type decoration


class StepikDispatcher:
    def __init__(self, client_id: str, client_secret: str):
        auth = HTTPBasicAuth(client_id, client_secret)
        resp = requests.post('https://stepik.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
        self.token: str = json.loads(resp.text)['access_token']
        # TODO: add check whether we get the token?

    def authorized_get(self, url: str) -> str:
        return requests.get(url, headers={'Authorization': 'Bearer ' + self.token}).text

    def get_and_parse_authorized(self, url: str) -> Dict:
        return json.loads(self.authorized_get(url))

    def get_course_page(self, course_id: ID) -> Dict:
        return self.get_and_parse_authorized('http://stepik.org/api/courses/' + str(course_id))

    def get_unit_ids_list(self, week_id: ID) -> List[ID]:
        return self.get_and_parse_authorized('https://stepik.org/api/sections/' + str(week_id))['sections'][0]['units']

    def get_lesson_id(self, unit_id: ID) -> ID:
        return self.get_and_parse_authorized('https://stepik.org/api/units/' + str(unit_id))['units'][0]['lesson']

    def get_step_ids_list(self, lesson_id: ID) -> List[ID]:
        return self.get_and_parse_authorized('https://stepik.org/api/lessons/' + str(lesson_id))['lessons'][0]['steps']

    def get_step(self, step_id: ID) -> Dict:
        return self.get_and_parse_authorized('https://stepik.org/api/steps/' + str(step_id))


@dataclass
class StepikVideoUrl:
    available_qualities: List[Dict[str, str]]


def get_course_videos_urls_by_section(course_id: ID,
                                      stepik_dispatcher: StepikDispatcher,
                                      only_from_week_number: Optional[int] = None) -> List[List[StepikVideoUrl]]:
    # TODO: out of course data we only use week_ids!!!
    course_data = stepik_dispatcher.get_course_page(course_id)

    def get_all_week_ids(stepik_resp):
        return stepik_resp['courses'][0]['sections']

    week_ids = get_all_week_ids(course_data)

    all_unit_ids = [stepik_dispatcher.get_unit_ids_list(week_id) for week_id in week_ids]

    videos_by_section: List[List[StepikVideoUrl]] = []
    for week_num in range(1, len(week_ids) + 1):
        if only_from_week_number is not None and week_num != only_from_week_number:
            continue

        all_lesson_ids = [stepik_dispatcher.get_lesson_id(unit_id) for unit_id in all_unit_ids[week_num - 1]]
        all_step_ids = [stepik_dispatcher.get_step_ids_list(lesson_id) for lesson_id in all_lesson_ids]
        all_step_ids = [step_id for steps_list in all_step_ids for step_id in steps_list]  # flattening list of step_ids

        all_steps_data = [stepik_dispatcher.get_step(step_id) for step_id in all_step_ids]

        def step_has_video(step_data) -> bool:
            return step_data['steps'][0]['block']['video']

        only_video_blocks = [step_info['steps'][0]['block'] for step_info in all_steps_data if step_has_video(step_info)]
        week_videos = [StepikVideoUrl(available_qualities=block['video']['urls']) for block in only_video_blocks]
        videos_by_section.append(week_videos)
    return videos_by_section


def parse_arguments():
    """
    Parse input arguments with help of argparse.
    """

    parser = argparse.ArgumentParser(
        description='Stepik downloader')

    parser.add_argument('-c', '--client_id',
                        help='your client_id from https://stepik.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-s', '--client_secret',
                        help='your client_secret from https://stepik.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-i', '--course_id',
                        help='course id',
                        type=int,
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
                        help='output directory. Default is the current folder',
                        default='.')

    args = parser.parse_args()

    return args


def reporthook(blocknum, blocksize, totalsize):  # progressbar
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


def main():
    args = parse_arguments()

    """
    Example how to receive token from Stepik.org
    Token should also been add to every request header
    example: requests.get(api_url, headers={'Authorization': 'Bearer '+ token})
    """
    stepik_dispatcher = StepikDispatcher(args.client_id, args.client_secret)

    video_urls_by_section = get_course_videos_urls_by_section(args.course_id, stepik_dispatcher, args.week_id)

    # Loop through all week in a course and
    # download all videos or
    # download only for the week_id is passed as an argument.
    for week_num, video_urls in enumerate(video_urls_by_section, start=1):

        url_list_with_q = []

        # Loop through videos and store the url link and the quality.
        for video in video_urls:
            video_link = None
            msg = None

            # Check a video quality.
            for link in video.available_qualities:
                match link:
                    case {'quality': args.quality, 'url': url}:
                        video_link = url
                        break

            # If there is no required video quality then download
            # with the best available quality.
            if video_link is None:
                msg = "The requested quality = {} is not available!".format(args.quality)

                video_link = video.available_qualities[0]['url']

            # Store link and quality.
            url_list_with_q.append({'url': video_link, 'msg': msg})

        # Compose a folder name.
        folder_name = os.path.join(args.output_dir, str(args.course_id), 'week_' + str(week_num))

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

        for video_num, el in enumerate(url_list_with_q):
            # Print a message if something wrong.
            if el['msg']:
                print("{}".format(el['msg']))

            filename = os.path.join(folder_name, 'Video_' + str(video_num) + '.mp4')
            if not os.path.isfile(filename):
                try:
                    print('Downloading file ', filename)
                    urllib.request.urlretrieve(el['url'], filename, reporthook)
                    print('Done')
                except urllib.error.ContentTooShortError:
                    os.remove(filename)
                    print('Error while downloading. File {} deleted:'.format(filename))
                except KeyboardInterrupt:
                    if os.path.isfile(filename):
                        os.remove(filename)
                    print('\nAborted')
                    exit(1)
            else:
                print('File {} already exist'.format(filename))
        print("All steps downloaded")


if __name__ == "__main__":
    main()
