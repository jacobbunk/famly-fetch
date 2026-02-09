<!-- @format -->

# famly-fetch

![Static Badge](https://img.shields.io/badge/Python-3-blue?style=flat&logo=Python)
![PyPI](https://img.shields.io/pypi/v/famly-fetch)

Fetch your (kid's) images from famly.co

**NOTICE: I no longer have access to Famly, so I am merely the steward of this
code base. If you create PRs with improvements or bugfixes, please make sure
to test them before submitting them.**

## Get Started

```
pip install famly-fetch
famly-fetch
```

Enter your email and password when prompted, or provide an access token for authentication. Run `famly-fetch --help` to
get full help page.

Downloaded images will be stored in the `pictures` directory of the
the folder where you run this program from.

By default, it will only download images where you have tagged your child. The
date that the photo was taken is embedded in its metadata and in its title.
For journey, notes and messages, the associated text is also added as an exif
comment unless disabled with `--no-text-comments`.

The images have been stripped for any metadata including EXIF
information by Famly. You can optionally add GPS coordinates to the EXIF
data of all downloaded images by providing latitude and longitude values.

The `--stop-on-existing` option is helpful if you wish to download
images continously and just want to download what is new since last
download.

### State management

famly-fetch tracks downloaded images in a state file to avoid re-downloading them.
By default, this state file is stored as `state.json` in your pictures folder.

You can customize the state file location using the `--state-file` option.

If you need to start over, simply delete (or move) the state file.

### Customizing Filenames

You can customize the filename format using the `--filename-pattern` option.
The pattern supports custom placeholders and standard strftime date/time formats.
The file extension is automatically appended.

**Custom placeholders:**

- `%FP` - Filename prefix (e.g., child name, "note", "message", "journey")
- `%ID` - Image ID

**Date/time formats:**
All standard strftime format codes are supported (e.g. `%Y`, `%m`, `%d` etc.)

**Default pattern:** `%FP-%Y-%m-%d_%H-%M-%S-%ID`

This produces filenames like: `child-name-2024-01-15_14-30-45-abc123.jpg`

[Hent-billeder-fra-Famly.co.pdf](Hent-billeder-fra-Famly.co.pdf)
contains instructions in Danish on how to make it work on a computer
running Windows.

## Command Line Help

```bash
Usage: famly-fetch [OPTIONS]

  Fetch kids' images from famly.co

Options:
  --email EMAIL                   Your famly.co email address, can be set via
                                  FAMLY_EMAIL env var
  --password PASSWORD             Your famly.co password, can be set via
                                  FAMLY_PASSWORD env var
  --access-token TOKEN            Your famly.co access token, can be set via
                                  FAMLY_ACCESS_TOKEN env var
  --famly-base-url URL            Your famly.co instance baseurl (default:
                                  https://app.famly.co), can be set via
                                  FAMLY_BASE_URL env var
  --no-tagged                     Don't download tagged images
  -j, --journey                   Download images from child Learning Journey
  -n, --notes                     Download images from child notes
  -m, --messages                  Download images from messages
  -l, --liked                     Download images which is liked by the
                                  parents from all posts (in the feed)
  -p, --pictures-folder DIRECTORY
                                  Directory to save downloaded pictures, can
                                  be set via FAMLY_PICTURES_FOLDER env var
                                  [default: pictures]
  -e, --stop-on-existing          Stop downloading when an already downloaded
                                  file is encountered
  -u, --user-agent                User Agent used in Famly requests, can be
                                  set via FAMLY_USER_AGENT env var  [default:
                                  famly-fetch/0.4.0]
  --latitude LAT                  Latitude for EXIF GPS data, can be set via
                                  LATITUDE env var
  --longitude LONG                Longitude for EXIF GPS data, can be set via
                                  LONGITUDE env var
  --text-comments / --no-text-comments
                                  Add observation and message body text to
                                  image EXIF UserComment field
  --filename-pattern PATTERN      Filename pattern. Custom patterns: %FP
                                  (prefix), %ID (image ID). Supports strftime
                                  formats (e.g., %Y, %m, %d). File extension
                                  is automatically appended. Can be set via
                                  FAMLY_FILENAME_PATTERN env var  [default:
                                  %FP-%Y-%m-%d_%H-%M-%S-%ID]
  --state-file FILE               Path to state file for tracking downloaded
                                  images, can be set via FAMLY_STATE_FILE env
                                  var  [default: (<pictures-
                                  folder>/state.json)]
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

## Docker

If you have Docker set up you can easily run as follows:

Build the container:

```bash
docker build -t famly-fetch -f dev.Dockerfile .
docker run -it -v $PWD/pictures:/app/pictures famly-fetch
```

Or use docker compose workflow

```bash
docker compose build
docker compose run app
```
