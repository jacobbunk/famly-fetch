import hashlib
import json
import urllib.request
import uuid

from importlib_resources import files


def get_device_id() -> str:
    """
    Generates a consistent device identifier as an UUID string.
    This function retrieves the hardware address as a 48-bit positive integer using `uuid.getnode()`,
    converts it to a hexadecimal string, hashes it using MD5 to ensure privacy and consistency,
    and then formats the hash as a UUID string.
    Returns:
        str: A 128-bit UUID string representing the device identifier.
    """

    raw_id = hex(uuid.getnode())
    # Hash + convert to UUID format (ensures consistent 128-bit UUID string)
    return str(uuid.UUID(hashlib.md5(raw_id.encode()).hexdigest()))


class ApiClient:
    _access_token = None
    _base = "https://app.famly.co"

    def __init__(self, user_agent: str | None = None):
        """
        Initialize the ApiClient.

        Args:
            user_agent (str): The user agent to use for requests.
        """
        self._user_agent: str | None = user_agent
        self._device_id = get_device_id()

    def login(self, email, password):
        """
        Authenticate with the Famly API and store the access token for future requests.

        Args:
            email (str): The user's email address.
            password (str): The user's password.

        Raises:
            Exception: If the server returns a non-200 HTTP status code.
        """

        login_data = self.make_graphql_request(
            "Authenticate",
            {
                "email": email,
                "password": password,
                "deviceId": self._device_id,
                "legacy": False,
            },
        )

        self._access_token = login_data["me"]["authenticateWithPassword"]["accessToken"]

    def get_child_notes(self, childId, cursor=None, first=10):
        data = self.make_graphql_request(
            "GetChildNotes",
            {
                "noteTypes": ["Classic"],
                "childId": childId,
                "parentVisible": True,
                "safeguardingConcern": False,
                "sensitive": False,
                "limit": first,
                "cursor": cursor,
            },
        )

        return data["childNotes"]

    def learning_journey_query(self, childId, cursor=None, first=10):
        data = self.make_graphql_request(
            "LearningJourneyQuery",
            {
                "childId": childId,
                "variants": [
                    "REGULAR_OBSERVATION",
                    "PARENT_OBSERVATION",
                ],
                "first": first,
                "next": cursor,
            },
        )

        return data["childDevelopment"]["observations"]

    def make_graphql_request(self, method, variables):
        query = files("famly_fetch.graphql").joinpath(f"{method}.graphql").read_text()

        postBody = {"operationName": method, "variables": variables, "query": query}

        data = self.make_api_request(
            "POST",
            f"/graphql?{method}",
            body=postBody,
        )

        return data["data"]

    def make_api_request(self, method, path, body=None, params=None):
        """
        Make a request to the Famly API and return the response.

        Args:
            method (str): The HTTP method to use for the request (e.g., "GET", "POST").
            path (str): The path of the API endpoint (e.g., "/graphql?Authenticate").
            body (dict, optional): The body of the request. Defaults to None.
            params (dict, optional): The query parameters to include in the request. Defaults to None.

        Returns:
            dict: The JSON response from the server.

        Raises:
            urllib.error.HTTPError: If the server couldn't fulfill the request.
            Exception: If the server returns a non-200 HTTP status code.
        """

        b = None
        if body:
            b = json.dumps(body).encode("utf-8")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._user_agent:
            headers["User-Agent"] = self._user_agent

        # If we already have the token, use it
        if self._access_token:
            headers["x-famly-accesstoken"] = self._access_token

        url = self._base + path

        if params:
            query_string = urllib.parse.urlencode(params)
            url += "?" + query_string

        req = urllib.request.Request(url=url, headers=headers, method=method, data=b)
        try:
            with urllib.request.urlopen(req) as f:
                body = f.read().decode("utf-8")
                if f.status != 200:
                    raise Exception(f"Broken! {body}")

                try:
                    return json.loads(body)
                except Exception as _e:
                    return body
        except urllib.error.HTTPError as e:
            # The server couldn't fulfill the request
            print("Error code: ", e.code)
            print("Response body: ", e.read())

    def me_me_me(self):
        """
        Get information about the currently authenticated user.

        Returns:
            dict: The JSON response from the server.

        Raises:
            urllib.error.HTTPError: If the server couldn't fulfill the request.
            Exception: If the server returns a non-200 HTTP status code.
        """

        return self.make_api_request("GET", "/api/me/me/me")
