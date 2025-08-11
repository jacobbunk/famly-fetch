# famly-fetch
Fetch your (kid's) images from famly.co

You need python3 installed and then it's as simple as running:


```
pip install .
./fetch.py <email> <password>
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

## Mac users

If you are on a Mac (which apparently comes with Python) the easiest
way is probably to fire up a Terminal and then run the following
commands (copy and paste carefully, one at a time):


```
mkdir famly
cd famly
curl -o fetch.py https://raw.githubusercontent.com/jacobbunk/famly-fetch/main/fetch.py
python3 ./fetch.py <email> <password>
```

This should have created a folder called ```famly``` where all your
images have been downloaded to.

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
