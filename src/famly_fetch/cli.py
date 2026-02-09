from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import click

from famly_fetch.downloader import FamlyDownloader


def get_version():
    try:
        return version("famly-fetch")
    except PackageNotFoundError:
        return "unknown"


@click.command()
@click.option(
    "--email",
    envvar="FAMLY_EMAIL",
    help="Your famly.co email address, can be set via FAMLY_EMAIL env var",
    metavar="EMAIL",
    type=str,
)
@click.option(
    "--password",
    envvar="FAMLY_PASSWORD",
    help="Your famly.co password, can be set via FAMLY_PASSWORD env var",
    metavar="PASSWORD",
    hide_input=True,
    type=str,
)
@click.option(
    "--access-token",
    envvar="FAMLY_ACCESS_TOKEN",
    help="Your famly.co access token, can be set via FAMLY_ACCESS_TOKEN env var",
    metavar="TOKEN",
    type=str,
)
@click.option(
    "--famly-base-url",
    envvar="FAMLY_BASE_URL",
    help="Your famly.co instance baseurl (default: https://app.famly.co), can be set via FAMLY_BASE_URL env var",
    metavar="URL",
    default="https://app.famly.co",
    type=str,
)
@click.option("--no-tagged", is_flag=True, help="Don't download tagged images")
@click.option(
    "-j", "--journey", is_flag=True, help="Download images from child Learning Journey"
)
@click.option("-n", "--notes", is_flag=True, help="Download images from child notes")
@click.option("-m", "--messages", is_flag=True, help="Download images from messages")
@click.option(
    "-l",
    "--liked",
    is_flag=True,
    help="Download images which is liked by the parents from all posts (in the feed)",
)
@click.option(
    "-p",
    "--pictures-folder",
    envvar="FAMLY_PICTURES_FOLDER",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default="pictures",
    show_default=True,
    help="Directory to save downloaded pictures, can be set via FAMLY_PICTURES_FOLDER env var",
)
@click.option(
    "-e",
    "--stop-on-existing",
    is_flag=True,
    help="Stop downloading when an already downloaded file is encountered",
)
@click.option(
    "-u",
    "--user-agent",
    envvar="FAMLY_USER_AGENT",
    default=f"famly-fetch/{get_version()}",
    help="User Agent used in Famly requests, can be set via FAMLY_USER_AGENT env var",
    metavar="",
    show_default=True,
    type=str,
)
@click.option(
    "--latitude",
    envvar="LATITUDE",
    type=float,
    help="Latitude for EXIF GPS data, can be set via LATITUDE env var",
    metavar="LAT",
)
@click.option(
    "--longitude",
    envvar="LONGITUDE",
    type=float,
    help="Longitude for EXIF GPS data, can be set via LONGITUDE env var",
    metavar="LONG",
)
@click.option(
    "--text-comments/--no-text-comments",
    is_flag=True,
    default=True,
    help="Add observation and message body text to image EXIF UserComment field",
)
@click.option(
    "--filename-pattern",
    envvar="FAMLY_FILENAME_PATTERN",
    default="%FP-%Y-%m-%d_%H-%M-%S-%ID",
    show_default=True,
    help="Filename pattern. Custom patterns: %FP (prefix), %ID (image ID). Supports strftime formats (e.g., %Y, %m, %d). File extension is automatically appended. Can be set via FAMLY_FILENAME_PATTERN env var",
    metavar="PATTERN",
    type=str,
)
@click.option(
    "--state-file",
    envvar="FAMLY_STATE_FILE",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=None,
    show_default="<pictures-folder>/state.json",
    help="Path to state file for tracking downloaded images, can be set via FAMLY_STATE_FILE env var",
    metavar="FILE",
)
@click.version_option()
def main(
    email: str,
    password: str,
    access_token: str,
    famly_base_url: str,
    no_tagged: bool,
    journey: bool,
    notes: bool,
    messages: bool,
    liked: bool,
    pictures_folder: Path,
    stop_on_existing: bool,
    user_agent: str,
    latitude: float,
    longitude: float,
    text_comments: bool,
    filename_pattern: str,
    state_file: Path,
):
    """Fetch kids' images from famly.co"""

    if state_file is None:
        state_file = pictures_folder / "state.json"

    # Validate authentication parameters
    if not access_token and (not email or not password):
        if not email:
            email = click.prompt("Enter your famly.co email address", type=str)
        if not password:
            password = click.prompt(
                "Enter your famly.co password", hide_input=True, type=str
            )

    if access_token and (email or password):
        click.secho(
            "Warning: Both access token and email/password provided. Using access token.",
            fg="yellow",
        )

    try:
        famly_downloader = FamlyDownloader(
            email=email,
            password=password,
            famly_base_url=famly_base_url,
            pictures_folder=pictures_folder,
            stop_on_existing=stop_on_existing,
            text_comments=text_comments,
            state_file=state_file,
            user_agent=user_agent,
            access_token=access_token,
            latitude=latitude,
            longitude=longitude,
            filename_pattern=filename_pattern,
        )

        if messages:
            famly_downloader.download_images_from_messages()

        # Process each child
        parent_ids = set()
        for child_id, first_name in famly_downloader.get_all_children():
            parent_ids |= famly_downloader.get_parents_ids(child_id)
            if not no_tagged:
                famly_downloader.download_tagged_images(child_id, first_name)
            if journey:
                famly_downloader.download_images_from_learning_journey(
                    child_id, first_name
                )
            if notes:
                famly_downloader.download_images_from_notes(child_id, first_name)

        if liked:
            famly_downloader.download_images_from_feed(parent_ids)

    except Exception as e:
        click.secho(f"An exception occurred: {e}", fg="red")


if __name__ == "__main__":
    main()
