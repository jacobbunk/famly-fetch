# famly-fetch
Fetch your (kid's) images from famly.co

You need python3 installed and then it's as simple as running:

```
./fetch.py <email> <password>
```

Notice that this will make your password visible in the process list
while the program is running, so only run this on a personal computer.

Downloaded images will be stored in the current working directory,
usually the folder where you run this program from.

It will only download images where you have tagged your child. Images
will be saved in the order they are listed in Famly, which is usually
in chronological order, but dates are available.

The images have been stripped for any metadata including EXIF
information by Famly.
