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

    TParsedStepikResource = Dict

    def get_resources_list(self, api_resource: str, ids: List[ID], page: int = 1) -> List[TParsedStepikResource]:
        response = requests.get('http://stepik.org/api/' + api_resource,
                                params={"ids[]": ids, 'page': page},
                                headers={'Authorization': 'Bearer ' + self.token})
        match response.status_code:
            case 200:
                paginated_list = json.loads(response.text)
                resources_list = paginated_list[api_resource]
                if paginated_list['meta']['has_next']:
                    resources_list += self.get_resources_list(api_resource, ids, page + 1)
                return resources_list
            case 431:  # large header error code
                return self.get_resources_list(api_resource, ids[:len(ids) // 2]) + \
                       self.get_resources_list(api_resource, ids[len(ids) // 2:])
            case _:
                raise Exception(f"Cannot load resources from Stepik.org ({api_resource}): "
                                f"server responded with {response.status_code}")

    def get_list_of_week_ids(self, course_id: ID) -> List[ID]:
        return \
            self.get_and_parse_authorized('http://stepik.org/api/courses/' + str(course_id))['courses'][0]['sections']

    def get_lists_of_units(self, week_ids: List[ID]) -> List[List[ID]]:
        weeks_data = self.get_resources_list('sections', week_ids)
        return [w['units'] for w in weeks_data]

    def get_list_of_lessons_ids(self, unit_ids: List[ID]) -> List[ID]:  # since one unit contains one lesson
        units_data = self.get_resources_list('units', unit_ids)
        return [u['lesson'] for u in units_data]

    def get_lists_of_step_ids(self, lesson_ids: List[ID]) -> List[List[ID]]:
        lessons_data = self.get_resources_list('lessons', lesson_ids)
        return [l['steps'] for l in lessons_data]

    def get_list_of_step_data(self, step_ids: List[ID]) -> List[Dict]:
        return self.get_resources_list('steps', step_ids)


@dataclass
class StepikVideoUrl:
    available_qualities: List[Dict[str, str]]


def get_course_videos_urls_by_section(course_id: ID,
                                      stepik_dispatcher: StepikDispatcher,
                                      only_from_week_number: Optional[int] = None) -> List[List[StepikVideoUrl]]:
    week_ids = stepik_dispatcher.get_list_of_week_ids(course_id)

    all_unit_ids = stepik_dispatcher.get_lists_of_units(week_ids)

    videos_by_section: List[List[StepikVideoUrl]] = []
    for week_num in range(1, len(week_ids) + 1):
        if only_from_week_number is not None and week_num != only_from_week_number:
            continue

        all_lesson_ids = stepik_dispatcher.get_list_of_lessons_ids(all_unit_ids[week_num - 1])
        all_step_ids = stepik_dispatcher.get_lists_of_step_ids(all_lesson_ids)
        all_step_ids = [step_id for steps_list in all_step_ids for step_id in steps_list]  # flattening list of step_ids

        all_steps_data = stepik_dispatcher.get_list_of_step_data(all_step_ids)

        def step_has_video(step_data) -> bool:
            return step_data['block']['video']

        only_video_blocks = [step_info['block'] for step_info in all_steps_data if step_has_video(step_info)]
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
