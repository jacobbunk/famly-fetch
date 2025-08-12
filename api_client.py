import json
import urllib.request


class ApiClient:

    _access_token = None
    _base = "https://app.famly.co"

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
                "deviceId": "d2900c00-042d-4db2-a329-798fcd2f152e",
                "legacy": False,
            },
        )

        self._access_token = login_data["me"]["authenticateWithPassword"]["accessToken"]

    def get_child_notes(self, childId, next=None, first=10):
        data = self.make_graphql_request(
            "GetChildNotes",
            {
                "noteTypes": ["Classic"],
                "childId": childId,
                "parentVisible": True,
                "safeguardingConcern": False,
                "sensitive": False,
                "limit": first,
                "cursor": next,
            },
        )

        return data["childNotes"]

    def learning_journey_query(self, childId, next=None, first=10):
        data = self.make_graphql_request(
            "LearningJourneyQuery",
            {
                "childId": childId,
                "variants": [
                    "REGULAR_OBSERVATION",
                    "PARENT_OBSERVATION",
                ],
                "first": first,
                "next": next,
            },
        )

        return data["childDevelopment"]["observations"]

    def make_graphql_request(self, method, variables):
        with open(f"{method}.graphql", "r") as file:
            query = file.read()

        postBody = {"operationName": method, "variables": variables, "query": query}

        data = login_data = self.make_api_request(
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

        headers = {"Content-Type": "application/json"}
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
                    raise "B0rked! %" % body

                try:
                    return json.loads(body)
                except Exception as e:
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
