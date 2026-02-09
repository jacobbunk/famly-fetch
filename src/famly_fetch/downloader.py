#!/usr/bin/env python3

"""Fetch all famly.co pictures of your kid

Auth has two versions:

 - "non-v2" has a `?accessToken=XXX` as a GET-parameter
 - v2-urls demands a `x-famly-accesstoken: XXX` header

"""

import json
import os
import shutil
import time
import urllib.request
from datetime import datetime, timezone
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
        famly_base_url: str,
        pictures_folder: Path,
        stop_on_existing: bool,
        text_comments: bool,
        state_file: Path,
        user_agent: str | None = None,
        access_token: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        filename_pattern: str = "%FP-%Y-%m-%d_%H-%M-%S-%ID",
    ):
        self._pictures_folder: Path = pictures_folder
        self._pictures_folder.mkdir(parents=True, exist_ok=True)

        self.stop_on_existing = stop_on_existing
        self.latitude = latitude
        self.longitude = longitude
        self.text_comments = text_comments
        self.filename_pattern = filename_pattern
        self.state_file = state_file
        self.downloaded_images = self.load_state()

        self._apiClient = ApiClient(
            base_url=famly_base_url, user_agent=user_agent, access_token=access_token
        )
        if not access_token:
            self._apiClient.login(email, password)

    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.downloaded_images, f)

    def mark_as_downloaded(self, img_id: str):
        self.downloaded_images[img_id] = datetime.now(timezone.utc).isoformat()

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

    def get_parents_ids(self, child_id: str) -> set[str]:
        relations = self._apiClient.get_relations(child_id)
        return {x["loginId"] for x in relations if x["loginId"]}

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
                        img_dict,
                        date_override=date,
                        text_override=text if self.text_comments else None,
                    )
                    click.echo(f" - image {img.img_id} from note at {img.date}")

                    file_path = self.download_file_path(img, f"{first_name}-note")
                    if img.img_id in self.downloaded_images:
                        click.secho(
                            f"Image {img.img_id} already downloaded, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)
                    self.mark_as_downloaded(img.img_id)

            next_ref = batch["next"]

            if not next_ref:
                break

        self.save_state()

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
                        img_dict,
                        date_override=date,
                        text_override=text if self.text_comments else None,
                    )
                    click.echo(f" - image {img.img_id} from observation at {img.date}")

                    file_path = self.download_file_path(img, f"{first_name}-journey")
                    if img.img_id in self.downloaded_images:
                        click.secho(
                            f"Image {img.img_id} already downloaded, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)
                    self.mark_as_downloaded(img.img_id)

            next_cursor = batch["next"]

            if not next_cursor:
                break

        self.save_state()

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
            if img.img_id in self.downloaded_images:
                click.secho(
                    f"Image {img.img_id} already downloaded, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                    fg="yellow",
                )
                if self.stop_on_existing:
                    return
                else:
                    continue

            # sleep for 1s to avoid 400 errors
            time.sleep(1)
            self.fetch_image(img, file_path)
            self.mark_as_downloaded(img.img_id)

        self.save_state()

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
                        img_dict,
                        date_override=date,
                        text_override=text if self.text_comments else None,
                    )

                    click.echo(f" - image {img.img_id} from message at {img.date}")

                    file_path = self.download_file_path(img, "message")

                    if img.img_id in self.downloaded_images:
                        click.secho(
                            f"Image {img.img_id} already downloaded, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    self.fetch_image(img, file_path)
                    self.mark_as_downloaded(img.img_id)

        self.save_state()

    def download_images_from_feed(self, liked_by_ids: set[str]):
        click.secho("Downloading liked images in posts...", fg="green")

        cursor = None
        older_than = None
        while True:
            click.echo("Fetching next 10 Posts")
            response = self._apiClient.feed(
                cursor=cursor, older_than=older_than, limit=10
            )
            if not response["feedItems"]:
                break
            last_item = response["feedItems"][-1]
            cursor = last_item["feedItemId"]
            older_than = last_item["createdDate"]
            for feed_item in response["feedItems"]:
                if not feed_item["originatorId"].startswith("Post:"):
                    # not a Post item
                    continue
                create_date = feed_item["createdDate"]
                for img_dict in feed_item["images"]:
                    if not (
                        img_dict["liked"]
                        or [
                            like
                            for like in img_dict["likes"]
                            if like["loginId"] in liked_by_ids
                        ]
                    ):
                        # not liked by parents
                        continue
                    img = Image.from_dict(
                        img_dict,
                        date_override=create_date,
                        text_override=feed_item["body"] if self.text_comments else None,
                    )
                    click.echo(f" - image {img.img_id} from post at {create_date}")

                    if img.img_id in self.downloaded_images:
                        click.secho(
                            f"Image {img.img_id} already downloaded, {'stopping download' if self.stop_on_existing else 'skipping'}.",
                            fg="yellow",
                        )
                        if self.stop_on_existing:
                            return
                        else:
                            continue
                    file_path = self.download_file_path(img, "post")
                    self.fetch_image(img, file_path)
                    self.mark_as_downloaded(img.img_id)

        self.save_state()

    def download_file_path(self, img: BaseImage, filename_prefix: str) -> Path:
        """Generate the file path for the downloaded image."""

        file_ext = os.path.splitext(urlparse(img.url).path)[1].lower()

        # Replace custom patterns first (to avoid collisions with strftime patterns)
        filename = self.filename_pattern
        filename = filename.replace("%FP", filename_prefix)
        filename = filename.replace("%ID", img.img_id)

        filename = img.date.strftime(filename)
        filename = filename + file_ext

        return Path(self._pictures_folder, filename)

    def fetch_image(self, img: BaseImage, file_path: Path):
        req = urllib.request.Request(url=img.url)

        captured_date_for_exif = img.date.strftime("%Y:%m:%d %H:%M:%S")

        if img.date.tzinfo is not None:
            timezone_offset = img.date.strftime("%z")
            # Convert from +0200 to +02:00 format
            if len(timezone_offset) == 5:
                timezone_offset = timezone_offset[:3] + ":" + timezone_offset[3:]
        else:
            timezone_offset = None

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

        if timezone_offset:
            exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal] = (
                timezone_offset.encode()
            )

        if img.text:
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
                piexif.helper.UserComment.dump(img.text, encoding="unicode")
            )

        # Add GPS data if latitude and longitude are provided
        if self.latitude is not None and self.longitude is not None:
            from fractions import Fraction

            def to_deg(value, loc):
                if value < 0:
                    loc_value = loc[0]
                elif value > 0:
                    loc_value = loc[1]
                else:
                    loc_value = ""
                abs_value = abs(value)
                deg = int(abs_value)
                t1 = (abs_value - deg) * 60
                min_val = int(t1)
                sec = round((t1 - min_val) * 60, 2)
                return deg, min_val, sec, loc_value

            def to_rational(number):
                f = Fraction(number).limit_denominator(10000)
                return (f.numerator, f.denominator)

            lat_deg = to_deg(self.latitude, ["S", "N"])
            lng_deg = to_deg(self.longitude, ["W", "E"])

            exiv_lat = (
                to_rational(lat_deg[0]),
                to_rational(lat_deg[1]),
                to_rational(lat_deg[2]),
            )
            exiv_lng = (
                to_rational(lng_deg[0]),
                to_rational(lng_deg[1]),
                to_rational(lng_deg[2]),
            )

            exif_dict["GPS"] = {  # type: ignore[assignment]
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitudeRef: lat_deg[3].encode(),
                piexif.GPSIFD.GPSLatitude: exiv_lat,
                piexif.GPSIFD.GPSLongitudeRef: lng_deg[3].encode(),
                piexif.GPSIFD.GPSLongitude: exiv_lng,
            }

        exif_bytes = piexif.dump(exif_dict)

        # Write the EXIF data to the image
        piexif.insert(exif_bytes, str(file_path.resolve()))
