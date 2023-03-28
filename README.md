# Python for RACE

This repo provides scripts to custom-build the
[Python interpreter](https://python.org) for RACE.

## License

The Python interpreter is licensed under the Python Software Foundation
(PSF) license agreement.

Only the build scripts in this repo are licensed under Apache 2.0.

## Dependencies

Python has dependencies on the following custom-built libraries:

* libffi
* OpenSSL

## How To Build

The [ext-builder](https://github.com/tst-race/ext-builder) image is used to
build Python.

```
git clone https://github.com/tst-race/ext-builder.git
git clone https://github.com/tst-race/ext-python.git
./ext-builder/build.py \
    --target linux-x86_64 \
    ./ext-python
```

## Platforms

Python is built for the following platforms:

* `android-x86_64`
* `android-arm64-v8a`

It is also used on Linux but can be installed via `apt`.

## How It Is Used

Python is used directly by the RACE core.
