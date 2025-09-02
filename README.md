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

Enter your email and password when prompted. Run `famly-fetch --help` to
get full help page.

Downloaded images will be stored in the `pictures` directory of the
the folder where you run this program from.

By default, it will only download images where you have tagged your child. The
date that the photo was taken is embedded in its metadata and in its title.
For journey, notes and messages, the associated text is also added as an exif
comment.

The images have been stripped for any metadata including EXIF
information by Famly.

The `--stop-on-existing` option is helpful if you wish to download
images continously and just want to download what is new since last
download.

[Hent-billeder-fra-Famly.co.pdf](Hent-billeder-fra-Famly.co.pdf)
contains instructions in Danish on how to make it work on a computer
running Windows.

## Command Line Help

```bash
Usage: famly-fetch [OPTIONS]

  Fetch kids' images from famly.co

Options:
  --email EMAIL                   Your famly.co email address, can be set via
                                  FAMLY_EMAIL env var  [required]
  --password PASSWORD             Your famly.co password, can be set via
                                  FAMLY_PASSWORD env var  [required]
  --no-tagged                     Don't download tagged images
  -j, --journey                   Download images from child Learning Journey
  -n, --notes                     Download images from child notes
  -m, --messages                  Download images from messages
  -p, --pictures-folder DIRECTORY
                                  Directory to save downloaded pictures, can
                                  be set via FAMLY_PICTURES_FOLDER env var
                                  [default: pictures]
  -e, --stop-on-existing          Stop downloading when an already downloaded
                                  file is encountered
  -u, --user-agent                User Agent used in Famly requests, can be
                                  set via FAMLY_USER_AGENT env var  [default:
                                  famly-fetch/0.2.0]
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
