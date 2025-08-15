#!/usr/bin/env python3

"""Fetch all famly.co pictures of your kid

Auth has two versions:

 - "non-v2" has a `?accessToken=XXX` as a GET-parameter
 - v2-urls demands a `x-famly-accesstoken: XXX` header

"""

import argparse
import os
import shutil
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import piexif
import piexif.helper

from api_client import ApiClient


class FamlyDownloader:

    def __init__(self, email, password):
        self._pictures_folder: Path = Path("pictures")
        self._pictures_folder.mkdir(parents=True, exist_ok=True)

        self._apiClient = ApiClient()
        self._apiClient.login(email, password)

    def download_images_from_notes(self, child_id, first_name):
        next = None

        while True:
            print("Fetching next 100 notes")
            batch = self._apiClient.get_child_notes(child_id, next=next, first=100)
            print(f"{len(batch["result"])} fetched.")

            for i, note in enumerate(batch["result"]):
                text = note["text"] + " - " + note["createdBy"]["name"]["fullName"]
                date = note["createdAt"]

                for img in note["images"]:
                    url = self.get_secret_image_url(img)

                    print(f"Fetching image {img["id"]} for note {i}")

                    self.fetch_image(url, img["id"], first_name, date, text)

            next = batch["next"]

            if not next:
                break

    def download_images_from_learning_journey(self, child_id, first_name):
        next = None

        while True:
            print("Fetching next 100 learning journey entries")
            batch = self._apiClient.learning_journey_query(
                child_id, next=next, first=100
            )
            print(f"{len(batch["results"])} fetched.")

            for i, observation in enumerate(batch["results"]):
                text = (
                    observation["remark"]["body"]
                    + " - "
                    + observation["createdBy"]["name"]["fullName"]
                )
                date = observation["status"]["createdAt"]

                for img in observation["images"]:
                    url = self.get_secret_image_url(img)

                    print(f"Fetching image {img["id"]} for observation {i}")

                    self.fetch_image(url, img["id"], first_name, date, text)

            next = batch["next"]

            if not next:
                break

    def get_secret_image_url(self, img):
        return "%s/%s/%sx%s/%s?expires=%s" % (
            img["secret"]["prefix"],
            img["secret"]["key"],
            img["width"],
            img["height"],
            img["secret"]["path"],
            img["secret"]["expires"],
        )

    def get_image_url(self, img):
        return "%s/%sx%s/%s" % (
            img["prefix"],
            img["width"],
            img["height"],
            img["key"],
        )

    def download_tagged_images(self, child_id, first_name):
        """Download images by childId"""
        imgs = self._apiClient.make_api_request(
            "GET", "/api/v2/images/tagged", params={"childId": child_id}
        )

        print("Fetching %s tagged images for %s" % (len(imgs), first_name))

        for img_no, img in enumerate(imgs, start=1):
            print(" - image {} ({}/{})".format(img["imageId"], img_no, len(imgs)))

            url = self.get_image_url(img)

            # sleep for 1s to avoid 400 errors
            time.sleep(1)

            self.fetch_image(url, img["imageId"], first_name, img["createdAt"])

    def download_images_from_messages(self):
        conversationsIds = self._apiClient.make_api_request(
            "GET", "/api/v2/conversations"
        )

        for conv_id in conversationsIds:
            conversation = self._apiClient.make_api_request(
                "GET", "/api/v2/conversations/%s" % (conv_id["conversationId"])
            )

            for msg in conversation["messages"]:
                text = msg["body"] + " - " + msg["author"]["title"]
                date = msg["createdAt"]

                for img in msg["images"]:
                    url = self.get_image_url(img)

                    self.fetch_image(url, img["imageId"], "message", date, text)

    def fetch_image(self, url, id, first_name, date, text=None):
        req = urllib.request.Request(url=url)

        file_ext = os.path.splitext(urlparse(url).path)[1].lower()

        captured_date = datetime.fromisoformat(date).strftime("%Y-%m-%d_%H-%M-%S")
        captured_date_for_exif = datetime.fromisoformat(date).strftime(
            "%Y:%m:%d %H:%M:%S"
        )

        filename: Path = Path(
            self._pictures_folder,
            "{}-{}-{}{}".format(first_name, captured_date, id, file_ext),
        )

        if filename.exists():
            print(f"File {filename} already exists, skipping")
            return

        with urllib.request.urlopen(req) as r, open(filename, "wb") as f:
            if r.status != 200:
                raise "B0rked! %s" % r.read().decode("utf-8")
            shutil.copyfileobj(r, f)

        try:
            piexif.load(str(filename.resolve()))
        except piexif.InvalidImageDataError:
            print("Not a JPEG/TIFF or corrupted image, skip exif updating.")
            return
        
        # Prepare the EXIF data
        exif_dict = {
            "Exif": {piexif.ExifIFD.DateTimeOriginal: captured_date_for_exif.encode()}
        }

        if text:
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
                piexif.helper.UserComment.dump(text, encoding="unicode")
            )

        exif_bytes = piexif.dump(exif_dict)

        # Write the EXIF data to the image
        piexif.insert(exif_bytes, str(filename.resolve())


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Fetch kids' images from famly.co")
    parser.add_argument("email", help="Auth email")
    parser.add_argument("password", help="Auth password")
    parser.add_argument(
        "--no-tagged", action="store_true", help="Don't download tagged images"
    )
    parser.add_argument(
        "-j",
        "--journey",
        action="store_true",
        help="Download images from child Learning Journey",
    )
    parser.add_argument(
        "-n", "--notes", action="store_true", help="Download images from child notes"
    )
    parser.add_argument(
        "-m", "--messages", action="store_true", help="Download images from messages"
    )
    args = parser.parse_args()

    # Create the downloader
    famly_downloader = FamlyDownloader(args.email, args.password)

    my_info = famly_downloader._apiClient.me_me_me()

    if args.messages:
        famly_downloader.download_images_from_messages()

    all_children = []

    # Current children
    for role in my_info["roles2"]:
        all_children.append((role["targetId"], role["title"]))

    # Previous children (that's what they call it)
    prev_children = []
    for ele in my_info["behaviors"]:
        if ele["id"] == "ShowPreviousChildren":
            prev_children = ele["payload"]["children"]

    for child in prev_children:
        all_children.append((child["childId"], child["name"]["firstName"]))

    # Process each child
    for child_id, first_name in all_children:
        if not args.no_tagged:
            famly_downloader.download_tagged_images(child_id, first_name)
        if args.journey:
            famly_downloader.download_images_from_learning_journey(child_id, first_name)
        if args.notes:
            famly_downloader.download_images_from_notes(child_id, first_name)


if __name__ == "__main__":
    main()
