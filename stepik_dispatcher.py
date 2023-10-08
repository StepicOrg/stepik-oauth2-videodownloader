import json
from typing import Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

ID = int  # for type decoration


class StepikDispatcher:
    """Handles authorization on Stepik and retrieves its resources through API"""

    def __init__(self, client_id: str, client_secret: str,
                 auth_manager=HTTPBasicAuth,  # dependency injections for testing purposes
                 json_parser=json.loads,
                 net_manager=requests):
        auth = auth_manager(client_id, client_secret)
        resp = net_manager.post('https://stepik.org/oauth2/token/',
                                data={'grant_type': 'client_credentials'}, auth=auth)
        self.json_parser = json_parser
        self.net_manager = net_manager
        self.token: str = self.json_parser(resp.text)['access_token']
        # TODO: add check whether we get the token?

    def authorized_get(self, url: str, params: Optional[Dict] = None):  # return type is self.net_manager.Response obj
        return self.net_manager.get(url, headers={'Authorization': 'Bearer ' + self.token}, params=params)

    def get_and_parse_authorized(self, url: str) -> Dict:
        return self.json_parser(self.authorized_get(url).text)

    TParsedStepikResource = Dict

    def get_resources_list(self, api_resource: str, ids: List[ID], page: int = 1) -> List[TParsedStepikResource]:
        response = self.authorized_get('http://stepik.org/api/' + api_resource, params={"ids[]": ids, 'page': page})
        match response.status_code:
            case 200:
                paginated_list = self.json_parser(response.text)
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
        return [lesson['steps'] for lesson in lessons_data]

    def get_list_of_step_data(self, step_ids: List[ID]) -> List[Dict]:
        return self.get_resources_list('steps', step_ids)
