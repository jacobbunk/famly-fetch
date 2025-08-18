import re
import time
from dataclasses import dataclass
from pathlib import Path

import click
import schedule

from famly_fetch.downloader import FamlyDownloader


@dataclass
class ScheduleTime:
    hour: int
    minute: int


class ScheduleTimeParamType(click.ParamType):
    name = "schedule_time"

    def convert(self, value, param, ctx):
        if value is None:
            return value
        match = re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", value)
        if not match:
            self.fail("Schedule time must be in HH:MM 24-hour format.", param, ctx)
        hour, minute = map(int, value.split(":"))
        return ScheduleTime(hour=hour, minute=minute)


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
@click.option(
    "--stop-on-existing",
    is_flag=True,
    help="Stop downloading when an already downloaded file is encountered",
)
@click.option(
    "-s",
    "--schedule",
    "schedule_mode",
    envvar="FAMLY_SCHEDULE_TIME",
    type=ScheduleTimeParamType(),
    default=None,
    help="Run the download every day at the specified time (format: HH:MM)",
)
def main(
    email: str,
    password: str,
    no_tagged: bool,
    journey: bool,
    notes: bool,
    messages: bool,
    pictures_folder: Path,
    stop_on_existing: bool,
    schedule_mode: ScheduleTime | None = None,
):
    """Fetch kids' images from famly.co

    EMAIL: Your famly.co email address, can be set via FAMLY_EMAIL env var

    PASSWORD: Your famly.co password, can be set via FAMLY_PASSWORD env var
    """

    def download():
        try:
            famly_downloader = FamlyDownloader(
                email, password, pictures_folder, stop_on_existing=stop_on_existing
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

    if not schedule_mode:
        download()
    else:
        schedule.every().day.at(
            f"{schedule_mode.hour:02}:{schedule_mode.minute:02}"
        ).do(download)

        click.secho(
            f"Starting scheduled downloads at {schedule_mode.hour:02}:{schedule_mode.minute:02} everyday...",
            fg="green",
        )
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()
