#!/usr/bin/env python3

#
# Copyright 2023 Two Six Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Script to build python for RACE
"""

import logging
import os
import race_ext_builder as builder


def get_cli_arguments(name):
    """Parse command-line arguments to the script"""
    parser = builder.get_arg_parser(
        name,
        "3.7.16",
        2,
        __file__,
        [builder.TARGET_ANDROID_x86_64, builder.TARGET_ANDROID_arm64_v8a],
    )
    parser.add_argument(
        "--libffi-version",
        default="3.3-1",
        help="Version of libffi dependency",
        type=str,
    )
    parser.add_argument(
        "--openssl-version",
        default="1.1.1l-1",
        help="Version of OpenSSL dependency",
        type=str,
    )
    parser.add_argument(
        "--skip-python-lib",
        action="store_true",
        help="Skip building of Python library",
    )
    parser.add_argument(
        "--skip-python-packages",
        action="store_true",
        help="Skip building of Python packages",
    )
    return builder.normalize_args(parser.parse_args())


def build_python_lib():
    args = get_cli_arguments("python")
    builder.make_dirs(args)
    builder.setup_logger(args)

    # Have to have host Python 3.7 installed even when cross-compiling
    # because it invokes the host python to generate build flags
    logging.root.info("Installing host python3.7")
    builder.execute(args, ["apt-get", "update", "-y"])
    builder.execute(args, ["add-apt-repository", "ppa:deadsnakes/ppa", "-y"])
    builder.install_packages(
        args,
        [
            "pkg-config=0.29.1*",
            "python3.7",
            "python3.7-dev",
            "python3.7-distutils",
            "python3.7-tk",
        ],
    )
    builder.execute(
        args,
        [
            "update-alternatives",
            "--install",
            "/usr/bin/python3",
            "python3",
            "/usr/bin/python3.7",
            "1",
        ],
    )
    builder.execute(
        args, ["update-alternatives", "--set", "python3", "/usr/bin/python3.7"]
    )

    builder.install_ext(
        args,
        [
            ("libffi", args.libffi_version),
            ("openssl", args.openssl_version),
        ],
    )

    if args.skip_python_lib:
        logging.root.info("Skipping build of Python library")
        return args.install_dir

    builder.fetch_source(
        args=args,
        source=f"https://www.python.org/ftp/python/{args.version}/Python-{args.version}.tgz",
        extract="tar.gz",
    )

    source_dir = os.path.join(args.source_dir, f"Python-{args.version}")
    env = builder.create_standard_envvars(args)
    env["CFLAGS"] = "-fPIC"
    env[
        "LDFLAGS"
    ] = f"-R/data/data/com.twosix.race/python3.7/lib-dynload -L{args.install_prefix}/lib/ -lffi"
    env["CXXFLAGS"] = "-fPIC -Wl,--export-dynamic -Wl,-lffi"
    env["OPENSSL_INCLUDES"] = f"{args.install_prefix}/include/"
    env["HAVE_X509_VERIFY_PARAM_SET1_HOST"] = "1"
    env["OPENSSL_LDFLAGS"] = f"-L{args.install_prefix}/lib/"
    env["OPENSSL_LIBS"] = "-lcrypto -lssl"
    env["CONFIG_SITE"] = "config.site"

    builder.copy(
        args,
        os.path.join(args.code_dir, "config.site"),
        source_dir,
    )
    builder.copy(
        args,
        os.path.join(args.code_dir, f"{args.target}.setup.py"),
        os.path.join(source_dir, "setup.py"),
    )

    logging.root.info("Configuring build")
    build = (
        "x86_64-pc-linux-gnu" if "x86" in os.uname().machine else "aarch64-pc-linux-gnu"
    )
    target = "x86_64-linux-android" if "x86" in args.target else "aarch64-linux-android"
    builder.execute(
        args,
        [
            "./configure",
            "--prefix=/",
            f"--host={target}",
            f"--build={build}",
            f"--target={target}",
            "--enable-shared",
            "--disable-ipv6",
            "--with-system-ffi",
        ],
        cwd=source_dir,
        env=env,
    )

    logging.root.info("Building")
    builder.execute(
        args,
        [
            "make",
            "-j",
            args.num_threads,
        ],
        cwd=source_dir,
        env=env,
    )
    builder.execute(
        args,
        [
            "make",
            f"DESTDIR={args.install_dir}",
            "install",
        ],
        cwd=source_dir,
        env=env,
    )

    builder.create_package(args)
    return args.install_dir


def build_python_packages(py_lib_dir):
    args = get_cli_arguments("python-packages")
    builder.make_dirs(args)
    builder.setup_logger(args)

    if args.skip_python_packages:
        logging.root.info("Skipping build of Python packages")
        return

    builder.install_packages(
        args,
        ["python3-pip"],
    )

    if args.target == builder.TARGET_ANDROID_x86_64:
        target_host = "x86_64-linux-android"
    elif args.target == builder.TARGET_ANDROID_arm64_v8a:
        target_host = "aarch64-linux-android"

    env = builder.create_standard_envvars(args)
    env["ANDROID_LIBRARY_DIRS"] = f"{args.install_prefix}/lib:{os.environ['ANDROID_NDK']}/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/{target_host}/29"
    env["ANDROID_INCLUDE_DIRS"] = f"{args.install_prefix}/include:{py_lib_dir}/include/python3.7m"
    env["LDSHARED"] = f"{env['CC']} --shared"
    env["PKG_CONFIG_PATH"] = f"{args.install_prefix}/lib/pkgconfig"

    logging.root.info("Copying standard python packages")
    builder.execute(args, ["rm", "-r", args.install_dir])
    builder.copy(args, os.path.join(py_lib_dir, "lib/python3.7"), args.install_dir)

    logging.root.info("Installing python packages from pip")
    builder.execute(args, ["python3", "-m", "pip", "install", "--upgrade", "pip"])
    builder.execute(args, [
        "python3",
        "-m",
        "pip",
        "download",
        "--requirement",
        os.path.join(args.code_dir, "requirements.txt"),
        "--dest",
        args.install_dir,
        "--platform",
        target_host,
        "--no-deps",
    ])

    logging.root.info("Building Python packages")
    builder.execute(args, [
        "bash",
        os.path.join(args.code_dir, "build_python_packages.sh"),
    ], cwd=args.install_dir, env=env)

    builder.create_package(args)


if __name__ == "__main__":
    py_lib_dir = build_python_lib()
    build_python_packages(py_lib_dir)
