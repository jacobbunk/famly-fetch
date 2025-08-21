#!/usr/bin/env python3

"""Fetch all famly.co pictures of your kid

Auth has two versions:

 - "non-v2" has a `?accessToken=XXX` as a GET-parameter
 - v2-urls demands a `x-famly-accesstoken: XXX` header

"""

import os
import shutil
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import click
import piexif
import piexif.helper

from famly_fetch.api_client import ApiClient
from famly_fetch.image import BaseImage, Image, SecretImage


class FamlyDownloader:
    def __init__(
        self,
        email: str,
        password: str,
        pictures_folder: Path,
        stop_on_existing: bool,
        user_agent: str | None = None,
    ):
        self._pictures_folder: Path = pictures_folder
        self._pictures_folder.mkdir(parents=True, exist_ok=True)

        self.stop_on_existing = stop_on_existing

        self._apiClient = ApiClient(user_agent)
        self._apiClient.login(email, password)

    def get_all_children(self):
        my_info = self._apiClient.me_me_me()
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

        return all_children

    def download_images_from_notes(self, child_id, first_name):
        click.secho(
            f"Downloading learning journey images for {first_name}...", fg="green"
        )
        next_ref = None

        while True:
            click.echo("Fetching next 100 notes")
            batch = self._apiClient.get_child_notes(
                child_id, cursor=next_ref, first=100
            )
            click.echo(f"{len(batch['result'])} fetched.")

            for _i, note in enumerate(batch["result"]):
                text = note["text"] + " - " + note["createdBy"]["name"]["fullName"]
                date = note["createdAt"]

                for img_dict in note["images"]:
                    img = SecretImage.from_dict(
                        img_dict, date_override=date, text_override=text
                    )
                    click.echo(f" - image {img.img_id} from note at {img.date}")

                    file_path = self.download_file_path(img, f"{first_name}-note")
                    if file_path.is_file and file_path.exists():
                        click.secho(
                            f"File {file_path} already exists, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)

            next_ref = batch["next"]

            if not next_ref:
                break

    def download_images_from_learning_journey(self, child_id, first_name):
        click.secho(
            f"Downloading learning journey images for {first_name}...", fg="green"
        )

        next_cursor = None

        while True:
            click.echo("Fetching next 100 learning journey entries")
            batch = self._apiClient.learning_journey_query(
                child_id, cursor=next_cursor, first=100
            )
            click.echo(f"{len(batch['results'])} fetched.")

            for _i, observation in enumerate(batch["results"]):
                text = (
                    observation["remark"]["body"]
                    + " - "
                    + observation["createdBy"]["name"]["fullName"]
                )
                date = observation["status"]["createdAt"]

                for img_dict in observation["images"]:
                    img = SecretImage.from_dict(
                        img_dict, date_override=date, text_override=text
                    )
                    click.echo(f" - image {img.img_id} from observation at {img.date}")

                    file_path = self.download_file_path(img, f"{first_name}-journey")
                    if file_path.is_file and file_path.exists():
                        click.secho(
                            f"File {file_path} already exists, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)

            next_cursor = batch["next"]

            if not next_cursor:
                break

    def download_tagged_images(self, child_id, first_name):
        """Download images by childId"""
        click.secho(f"Downloading tagged images for {first_name}...", fg="green")

        imgs = self._apiClient.make_api_request(
            "GET", "/api/v2/images/tagged", params={"childId": child_id}
        )

        click.echo(f"Fetching {len(imgs)} tagged images for {first_name}")

        for img_no, img_dict in enumerate(imgs, start=1):
            img = Image.from_dict(img_dict)
            click.echo(f" - image {img.img_id} at {img.date} ({img_no}/{len(imgs)})")

            file_path = self.download_file_path(img, first_name)
            if file_path.is_file and file_path.exists():
                click.secho(
                    f"File {file_path} already exists, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                    fg="yellow",
                )
                if self.stop_on_existing:
                    return
                else:
                    continue

            # sleep for 1s to avoid 400 errors
            time.sleep(1)
            self.fetch_image(img, file_path)

    def download_images_from_messages(self):
        click.secho("Downloading images from messages...", fg="green")

        conv_ids = self._apiClient.make_api_request("GET", "/api/v2/conversations")
        click.echo(f"Found {len(conv_ids)} conversations")

        for conv_id in reversed(conv_ids):
            conversation = self._apiClient.make_api_request(
                "GET", "/api/v2/conversations/%s" % (conv_id["conversationId"])
            )
            for msg in reversed(conversation["messages"]):
                text = msg["body"] + " - " + msg["author"]["title"]
                date = msg["createdAt"]

                for img_dict in msg["images"]:
                    img = Image.from_dict(
                        img_dict, date_override=date, text_override=text
                    )

                    click.echo(f" - image {img.img_id} from message at {img.date}")

                    file_path = self.download_file_path(img, "message")

                    if file_path.is_file and file_path.exists():
                        click.secho(
                            f"File {file_path} already exists, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)

    def download_file_path(self, img: BaseImage, filename_prefix: str) -> Path:
        """Generate the file path for the downloaded image."""

        file_ext = os.path.splitext(urlparse(img.url).path)[1].lower()
        captured_date = img.date.strftime("%Y-%m-%d_%H-%M-%S")
        return Path(
            self._pictures_folder,
            f"{filename_prefix}-{captured_date}-{img.img_id}{file_ext}",
        )

    def fetch_image(self, img: BaseImage, file_path: Path):
        req = urllib.request.Request(url=img.url)

        captured_date_for_exif = img.date.strftime("%Y:%m:%d %H:%M:%S")

        with urllib.request.urlopen(req) as r, open(file_path, "wb") as f:
            if r.status != 200:
                raise Exception(f"Broken! {r.read().decode('utf-8')}")
            shutil.copyfileobj(r, f)

        try:
            piexif.load(str(file_path.resolve()))
        except piexif.InvalidImageDataError:
            click.secho(
                "Not a JPEG/TIFF or corrupted image, skip exif updating.", fg="yellow"
            )
            return

        # Prepare the EXIF data
        exif_dict = {
            "Exif": {piexif.ExifIFD.DateTimeOriginal: captured_date_for_exif.encode()}
        }

        if img.text:
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
                piexif.helper.UserComment.dump(img.text, encoding="unicode")
            )

        exif_bytes = piexif.dump(exif_dict)

        # Write the EXIF data to the image
        piexif.insert(exif_bytes, str(file_path.resolve()))
