#!/usr/bin/env python3

"""Fetch all famly.co pictures of your kid

Auth has two versions:

 - "non-v2" has a `?accessToken=XXX` as a GET-parameter
 - v2-urls demands a `x-famly-accesstoken: XXX` header

"""

import argparse
import json
import shutil
import urllib.request


class FamlyClient:
    _access_token = None

    def __init__(self, email, password):
        self._base = "https://app.famly.co"

        login_data = self.login(email, password)
        self._access_token = login_data["accessToken"]

    def _request_json(self, method, url, body=None):
        """Get some JSON and hope we get some back"""
        b = None
        if body:
            b = json.dumps(body).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["x-famly-accesstoken"] = self._access_token

        req = urllib.request.Request(url=url, headers=headers, method=method, data=b)

        with urllib.request.urlopen(req) as f:
            body = f.read().decode("utf-8")
            if f.status != 200:
                raise "B0rked! %" % body

            try:
                return json.loads(body)
            except Exception as e:
                return body

    def _auth_request(self, method, path, body=None, request_params=None):
        # This should perhaps be split in two functions, one for "classic"
        # requests and auth, and then one for the "v2"-stuff...
        if not request_params:
            request_params = {}

        if "v2" not in path:
            request_params["accessToken"] = self._access_token

        # Serialize request-params
        key_values = ["%s=%s" % (k, v) for k, v in request_params.items()]

        return self._request_json(
            method, self._base + path + "?" + ("&".join(key_values)), body
        )

    def login(self, email, password):
        """Get an access token"""
        return self._request_json(
            "POST",
            self._base + "/api/login/login/authenticate",
            body={"email": email, "password": password},
        )

    def me_me_me(self):
        """Know about thy self..."""
        return self._auth_request("GET", "/api/me/me/me")

    def download_images_by_child_id(self, child_id, first_name):
        """Download images by childId"""
        imgs = client._auth_request(
            "GET", "/api/v2/images/tagged", request_params={"childId": child_id}
        )

        print("Fetching %s images for %s" % (len(imgs), first_name))

        for img_no, img in enumerate(imgs, start=1):
            print(" - image {} ({}/{})".format(img["imageId"], img_no, len(imgs)))

            # This is constructed from very few examples - I might be asking it
            # to crop things it should not...
            url = "%s/%sx%s/%s" % (
                img["prefix"],
                img["height"],
                img["width"],
                img["key"],
            )

            req = urllib.request.Request(url=url)
            filename = "{}-{:06d}-{}.jpg".format(
                first_name, int(1e4) - img_no, img["imageId"]
            )

            with urllib.request.urlopen(req) as r, open(filename, "wb") as f:
                if r.status != 200:
                    raise "B0rked! %s" % body
                shutil.copyfileobj(r, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch kids' images from famly.co")
    parser.add_argument("email", help="Auth email")
    parser.add_argument("password", help="Auth password")
    args = parser.parse_args()
    client = FamlyClient(args.email, args.password)

    my_info = client.me_me_me()

    # Current children
    for role in my_info["roles2"]:
        client.download_images_by_child_id(role["targetId"], role["title"])

    # Previous children (that's what they call it)
    prev_children = []
    for ele in my_info["behaviors"]:
        if ele["id"] == "ShowPreviousChildren":
            prev_children = ele["payload"]["children"]

    for child in prev_children:
        client.download_images_by_child_id(child["childId"], child["name"]["firstName"])
