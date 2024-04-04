import json
import urllib.request

class ApiClient:

    _access_token = None
    _base = "https://app.famly.co"
    
    
    def login(self, email, password):
        """Get an access token"""

        postBody = {
            "operationName": "Authenticate",
            "variables": {
                "email": email,
                "password": password,
                "deviceId": "d2900c00-042d-4db2-a329-798fcd2f152e",
                "legacy": False,
            },
            "query": "mutation Authenticate($email: EmailAddress!, $password: Password!, $deviceId: DeviceId, $legacy: Boolean) {\n  me {\n    authenticateWithPassword(\n      email: $email\n      password: $password\n      deviceId: $deviceId\n      legacy: $legacy\n    ) {\n      ...AuthenticationResult\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AuthenticationResult on AuthenticationResult {\n  status\n  __typename\n  ... on AuthenticationFailed {\n    status\n    errorDetails\n    errorTitle\n    __typename\n  }\n  ... on AuthenticationSucceeded {\n    accessToken\n    deviceId\n    __typename\n  }\n  ... on AuthenticationChallenged {\n    ...AuthChallenge\n    __typename\n  }\n}\n\nfragment AuthChallenge on AuthenticationChallenged {\n  loginId\n  deviceId\n  expiresAt\n  choices {\n    context {\n      ...UserContextFragment\n      __typename\n    }\n    hmac\n    requiresTwoFactor\n    __typename\n  }\n  person {\n    name {\n      fullName\n      __typename\n    }\n    profileImage {\n      url\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UserContextFragment on UserContext {\n  id\n  target {\n    __typename\n    ... on PersonContextTarget {\n      person {\n        name {\n          fullName\n          __typename\n        }\n        __typename\n      }\n      children {\n        name {\n          firstName\n          fullName\n          __typename\n        }\n        profileImage {\n          url\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ... on InstitutionSet {\n      title\n      profileImage {\n        url\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}"
        }
        
        login_data = self.make_api_request(
            "POST",
            "/graphql?Authenticate",
            body=postBody,
        )
        
        self._access_token = login_data["data"]["me"]["authenticateWithPassword"]["accessToken"]

    def make_api_request(self, method, path, body=None, params = None):
            """Get some JSON and hope we get some back"""
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

            req = urllib.request.Request(
                url=url, headers=headers, method=method, data=b)
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
                print('Error code: ', e.code)
                print('Response body: ', e.read())

    def me_me_me(self):
        """Know about thy self..."""
        return self.make_api_request("GET", "/api/me/me/me")    
    
