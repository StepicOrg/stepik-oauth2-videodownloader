from stepik_dispatcher import StepikDispatcher
import pytest
import json


def mock_auth(*args, **kwargs):
    return None


class MockNet:
    class MockResponse:
        def __init__(self, text: str, code: int):
            self.text = text
            self.status_code = code

    def post(self, *args, **kwargs):  # OK answer during authentication
        return self.MockResponse(json.dumps({"access_token": "none"}), 200)


def test_init_wrong_credentials_raises_WrongCredentials_exception():
    class MockNetWrongCredentials(MockNet):
        def post(self, *args, **kwargs):
            return self.MockResponse(json.dumps({"access_token": "none"}), 401)

    with pytest.raises(StepikDispatcher.WrongCredentials):
        StepikDispatcher("wrong_id", "wrogn_secret", mock_auth, json.loads, MockNetWrongCredentials())

def test_init_authentication_fail_with_correct_credentials_raises_AuthenticationFailure():
    class MockNetCorrectCredentials(MockNet):
        def post(self, *args, **kwargs):
            return self.MockResponse(json.dumps({"access_token": "none"}), 501)

    with pytest.raises(StepikDispatcher.AuthenticationFailure):
        StepikDispatcher("wrong_id", "wrogn_secret", mock_auth, json.loads, MockNetCorrectCredentials())


def test_get_resources_list_correct_resource_one_page_correct():
    requested_ids = [1, 7, 984, 56, 10, 0, 1332, 88913, 193, 484, 4, 5, 8, 1]
    expected_list = [{"id": i, "price": "priceless"} for i in requested_ids]
    RESOURCE_NAME = "precious"

    class MockNetSinglePageResource(MockNet):
        def get(self, *args, **kwargs):
            resp_text = json.dumps({"meta": {"has_next": False}, RESOURCE_NAME: expected_list})
            return self.MockResponse(resp_text, 200)

    stepik_dispatcher = StepikDispatcher("correct_client", "correct_secret",
                                         mock_auth, json.loads, MockNetSinglePageResource())

    assert stepik_dispatcher.get_resources_list(RESOURCE_NAME, requested_ids) == expected_list


def test_get_resources_list_resource_pages_concatenated_correctly():
    requested_ids = [1, 7, 984, 56, 10, 0, 1332, 88913, 193, 484, 4, 5, 8, 1]
    MAX_ON_PAGE = 5
    expected_list = [{"id": i, "price": "priceless"} for i in requested_ids]
    RESOURCE_NAME = "precious"

    class MockNetMultiplePageConcatenation(MockNet):
        def get(self, url, params, *args, **kwargs):
            page_index = params["page"]
            response = {"meta": {"has_next": bool(page_index * MAX_ON_PAGE <= len(expected_list))},
                        RESOURCE_NAME: expected_list[(page_index-1) * MAX_ON_PAGE: page_index * MAX_ON_PAGE]
                        }
            return self.MockResponse(json.dumps(response), 200)

    stepik_dispatcher = StepikDispatcher("correct_client", "correct_secret",
                                         mock_auth, json.loads, MockNetMultiplePageConcatenation())

    assert stepik_dispatcher.get_resources_list(RESOURCE_NAME, requested_ids) == expected_list

def test_get_resources_list_too_long_header_handled_correctly():
    requested_ids = [1, 7, 984, 56, 10, 0, 1332, 88913, 193, 484, 4, 5, 8, 11]
    db = {i: {"id": i, "price": "kinda_priceless"} for i in requested_ids}
    expected_list = [db[i] for i in requested_ids]
    MAX_NUM_OF_IDS = 9
    assert MAX_NUM_OF_IDS < len(requested_ids)

    RESOURCE_NAME = "not_so_precious"

    class MockNetLongHeader(MockNet):
        def get(self, url, params, *args, **kwargs):
            if len(params["ids[]"]) > MAX_NUM_OF_IDS:
                return self.MockResponse("", 431)
            response = {"meta": {"has_next": False},
                        RESOURCE_NAME: [db[i] for i in params["ids[]"]]
                        }
            return self.MockResponse(json.dumps(response), 200)

    stepik_dispatcher = StepikDispatcher("correct_client", "correct_secret",
                                         mock_auth, json.loads, MockNetLongHeader())

    assert stepik_dispatcher.get_resources_list(RESOURCE_NAME, requested_ids) == expected_list

def test_get_resources_list_server_error_raises_ResourceAcquisitionFailure():
    class MockNetInternalServerError(MockNet):
        def get(self, *args, **kwargs):
            return self.MockResponse("", 500)

    stepik_dispatcher = StepikDispatcher("wrong_id", "wrogn_secret",
                                         mock_auth, json.loads, MockNetInternalServerError())

    with pytest.raises(StepikDispatcher.ResourceAcquisitionFailure):
        stepik_dispatcher.get_resources_list("precious_resource", [1, 3, 5, 991])
