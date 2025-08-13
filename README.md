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
famly-fetch <email> <password>
```

Notice that this will make your password visible in the process list
while the program is running, so only run this on a personal computer.

Downloaded images will be stored in the ``pictures`` directory of the
the folder where you run this program from.

By default, it will only download images where you have tagged your child. The
date that the photo was taken is embedded in its metadata and in its title.
For journey, notes and messages, the associated text is also added as an exif
comment.

The images have been stripped for any metadata including EXIF
information by Famly.

[Hent-billeder-fra-Famly.co.pdf](Hent-billeder-fra-Famly.co.pdf)
contains instructions in Danish on how to make it work on a computer
running Windows.

## Arguments

| Argument | Description |
| --- | --- |
| `--no-tagged` | Don't download tagged images |
| `--journey` `-j` | Download images from child Learning Journey |
| `--notes` `-n` | Download images from child notes |
| `--messages` `-m` | Download images from messages |


## Docker

If you have Docker set up you can easily run as follows:

 Build the container:
```
docker build -t famly-fetch .
```

Run:
```
docker run -v $PWD/pictures:/usr/src/app/pictures famly-fetch <email> <password>
```
