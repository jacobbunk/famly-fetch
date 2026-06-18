<!-- @format -->

# famly-fetch

![Static Badge](https://img.shields.io/badge/Python-3-blue?style=flat&logo=Python)
![PyPI](https://img.shields.io/pypi/v/famly-fetch)

Fetch your (kid's) images from famly.co

**NOTICE: I no longer have access to Famly, so I am merely the steward of this
code base. If you create PRs with improvements or bugfixes, please make sure
to test them before submitting them.**

## Local Development

To run the project locally from source:

```bash
git clone https://github.com/ileodo/famly-fetch.git
cd famly-fetch
python -m venv .venv
```

Activate the virtual environment:

- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

Then install the package in editable mode:

```bash
pip install -e .
famly-fetch
```

To deactivate the virtual environment when done:

```bash
deactivate
```

## Running CI Locally

The GitHub Actions workflow (`.github/workflows/ci.yml`) lints and format-checks
the code across a matrix of Python versions (3.10, 3.11, 3.12, 3.13). You can
reproduce that workflow on your own machine before pushing, using the
`scripts/ci-local.sh` wrapper around [`act`](https://github.com/nektos/act).

It runs the exact same steps as GitHub (checkout, set up Python, install
dependencies, `ruff check`, `ruff format --diff`) inside Ubuntu containers, one
per matrix entry, so any failure you see locally matches what CI will report.

The workflow runs in a local Docker image built from `ci-local.Dockerfile`,
which extends the standard `act` runner with Node.js (the stock image has no
`node` on PATH, which the checkout and setup-python actions need). The wrapper
builds this image automatically on first run.

Requirements:

- [`act`](https://github.com/nektos/act) (`brew install act` on macOS)
- A running Docker daemon

Usage:

```bash
# Run all four matrix builds (3.10-3.13) concurrently
scripts/ci-local.sh

# Run only the Python 3.11 build
scripts/ci-local.sh -v 3.11

# List the jobs without running them
scripts/ci-local.sh -l

# Rebuild the local runner image (e.g. after editing ci-local.Dockerfile)
scripts/ci-local.sh -b

# Pass extra flags straight through to act
scripts/ci-local.sh -- --verbose
```

The first run builds the runner image, which can take a minute or two. On Apple
silicon the script automatically requests the `linux/amd64` image so the
containers match GitHub's runners. Run `scripts/ci-local.sh -h` for the full
list of options.

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

### Downloading all feed images

The `-f` / `--feed` flag downloads all images from all nursery feed posts, regardless of likes or tags:

```bash
famly-fetch -f
```

Images are organised into subdirectories named by the post date (e.g. `pictures/2026-02-19/`), so all photos from posts on the same day are grouped together.

> **Important privacy notice:** Using `-f` will download *all* images from the nursery feed, including photos of other children who are not your own. These images are shared by the nursery within a trusted setting. As a user of this tool you are solely responsible for handling these images with care — keep them private, do not share them further, and ensure they are stored securely. Delete any images of other children if you do not need them.

### State management

famly-fetch tracks downloaded images in a state file to avoid re-downloading them.
By default, this state file is stored as `state.json` in your pictures folder.

You can customize the state file location using the `--state-file` option.

If you need to start over, simply delete (or move) the state file.

### Downloading non-image attachments and videos

Use `--include-files` to download non-image file attachments (PDFs, documents, and similar files) from messages, notes, and learning journey entries:

```bash
famly-fetch --include-files
```

Use `--include-videos` to download videos from learning journey observations and feed posts:

```bash
famly-fetch --include-videos
```

Both flags can be combined with any other flags. They reuse the same `state.json` tracking and the same date-grouped folder layout as image downloads, so re-running will skip already-downloaded files. Non-image content is stored as-is without any EXIF metadata added.

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
  -f, --feed                      Download all images from all posts (in the
                                  feed)
  --include-files                 Also download non-image file attachments
                                  (PDFs, docs, etc.) from messages, notes, and
                                  journeys
  --include-videos                Also download videos from learning journey
                                  observations and feed posts
  -p, --pictures-folder DIRECTORY
                                  Directory to save downloaded pictures, can
                                  be set via FAMLY_PICTURES_FOLDER env var
                                  [default: pictures]
  -e, --stop-on-existing          Stop downloading when an already downloaded
                                  file is encountered
  -u, --user-agent                User Agent used in Famly requests, can be
                                  set via FAMLY_USER_AGENT env var  [default:
                                  famly-fetch/<version>]
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

## Known Issues

### Connection reset error

When downloading a large number of images, you may see:

```
An exception occurred: <urlopen error [WinError 10054] An existing connection was forcibly closed by the remote host>
```

This is caused by the Famly server closing the connection after too many requests. Simply re-run the same command — already downloaded images are tracked in `state.json` and will be skipped, so the download will resume from where it left off.

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
