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
    required=True,
    prompt="Enter your famly.co email address",
    help="Your famly.co email address, can be set via FAMLY_EMAIL env var",
    metavar="EMAIL",
    type=str,
)
@click.option(
    "--password",
    envvar="FAMLY_PASSWORD",
    required=True,
    prompt="Enter your famly.co password",
    help="Your famly.co password, can be set via FAMLY_PASSWORD env var",
    metavar="PASSWORD",
    hide_input=True,
    type=str,
)
@click.option("--no-tagged", is_flag=True, help="Don't download tagged images")
@click.option(
    "-j", "--journey", is_flag=True, help="Download images from child Learning Journey"
)
@click.option("-n", "--notes", is_flag=True, help="Download images from child notes")
@click.option("-m", "--messages", is_flag=True, help="Download images from messages")
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
@click.version_option()
def main(
    email: str,
    password: str,
    no_tagged: bool,
    journey: bool,
    notes: bool,
    messages: bool,
    pictures_folder: Path,
    stop_on_existing: bool,
    user_agent: str,
):
    """Fetch kids' images from famly.co"""

    try:
        famly_downloader = FamlyDownloader(
            email,
            password,
            pictures_folder,
            stop_on_existing=stop_on_existing,
            user_agent=user_agent,
        )

        if messages:
            famly_downloader.download_images_from_messages()

        # Process each child
        for child_id, first_name in famly_downloader.get_all_children():
            if not no_tagged:
                famly_downloader.download_tagged_images(child_id, first_name)
            if journey:
                famly_downloader.download_images_from_learning_journey(
                    child_id, first_name
                )
            if notes:
                famly_downloader.download_images_from_notes(child_id, first_name)
    except Exception as e:
        click.secho(f"An exception occurred: {e}", fg="red")


if __name__ == "__main__":
    main()
