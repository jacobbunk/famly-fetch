from pathlib import Path

import click

from famly_fetch.downloader import FamlyDownloader


@click.command()
@click.argument("email", envvar="FAMLY_EMAIL", type=str)
@click.argument("password", envvar="FAMLY_PASSWORD", type=str)
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
    help="Directory to save downloaded pictures",
)
def main(
    email: str,
    password: str,
    no_tagged: bool,
    journey: bool,
    notes: bool,
    messages: bool,
    pictures_folder: Path,
):
    """Fetch kids' images from famly.co

    EMAIL: Your famly.co email address, can be set via FAMLY_EMAIL env var

    PASSWORD: Your famly.co password, can be set via FAMLY_PASSWORD env var
    """
    famly_downloader = FamlyDownloader(email, password, pictures_folder)

    if messages:
        famly_downloader.download_images_from_messages()

    # Process each child
    for child_id, first_name in famly_downloader.get_all_children():
        if not no_tagged:
            famly_downloader.download_tagged_images(child_id, first_name)
        if journey:
            famly_downloader.download_images_from_learning_journey(child_id, first_name)
        if notes:
            famly_downloader.download_images_from_notes(child_id, first_name)


if __name__ == "__main__":
    main()
