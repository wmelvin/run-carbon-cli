#!/usr/bin/env python3

import shutil
import subprocess
import sys
import time
from pathlib import Path
from random import randint

from PIL import Image
from rich import print
from watchfiles import watch

__version__ = "0.1.dev5"

code_dir = Path.cwd() / "code_files"


def scale_image(src_image: Path, opts: dict) -> None:
    max_width = opts.get("image_max_width")
    if not max_width:
        return

    try:
        new_width = int(max_width)
    except ValueError:
        print(f"WARNING: Invalid image_max_width '{max_width}'")
        return

    with Image.open(src_image) as img:
        if img.size[0] <= new_width:
            return

        # Preserve the aspect ratio
        width_percent = (new_width / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))

        # Resize the image
        new_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # # Save the resized image
        # out_image = src_image.parent / f"{src_image.stem}-scaled{src_image.suffix}"
        # print(f"Saving scaled image '{out_image}'")
        # new_img.save(out_image)

        # Overwrite the original image
        print(f"Resized image '{src_image}'")
        new_img.save(src_image)


def get_app_options_from_file(config_dir: Path) -> dict:
    opts = {}
    opt_file = config_dir / "run_carbon_cli-options.txt"
    if opt_file.exists():
        for line in opt_file.read_text().splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            if "=" in s:
                n, v = line.split("=", 1)
                opts[n.strip()] = v.strip()
    return opts


def run_carbon():
    target_config = Path.home() / ".carbon-now.json"

    # If a file named 'carbon-now.json' is in the config_files directory
    # then use that configuration.
    config_dir = Path.cwd() / "config_files"
    use_config = config_dir / "carbon-now.json"
    if not use_config.exists():
        #  Otherwise use a default local config file.
        config_name = "config-onelight-hack"
        # config_name = "config-nightowl-hack"
        # config_name = "config-oceanicnext-hack"

        use_config = Path.cwd() / f"{config_name}-png.json"

    if not use_config.exists():
        sys.stderr.write(f"\nERROR: Config file '{use_config}' not found.\n")
        sys.exit(1)

    print(f"Using configuration '{use_config}'")

    opts = get_app_options_from_file(config_dir)

    print(f"Options: {opts}")

    # Replace the default config file with the config to use.
    # WARNING: This wipes out any presets saved manually via
    # the carbon-now CLI.
    shutil.copy2(use_config, target_config)

    out_dir = Path.cwd() / "images"
    if not out_dir.exists():
        out_dir.mkdir()

    carbon_cmd = shutil.which("carbon-now")
    if not carbon_cmd:
        sys.stderr.write("\nERROR: carbon-now CLI not found.\n")
        sys.exit(1)

    print(carbon_cmd)

    files = sorted([p for p in code_dir.iterdir() if p.is_file()])

    for file in files:
        print(f"\nSOURCE '{file}'")
        ext = "png"
        out_file = out_dir / f"codeimg_{file.stem}.{ext}"

        # Only replace an existing output file if the source is newer.
        if out_file.exists() and out_file.stat().st_mtime > file.stat().st_mtime:
            print(f"SKIP existing '{out_file.name}'")
            continue

        args = [
            carbon_cmd,
            str(file),
            "--save-to",
            str(out_dir),
            "--save-as",
            out_file.stem
        ]

        print(f"RUN '{' '.join(args)}'")

        result = subprocess.run(  # noqa: S603
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        if result.stdout is not None:
            print(f"\nSTDOUT:\n{result.stdout.strip()}\n")

        if result.stderr is not None:
            print(f"\nSTDERR:\n{result.stderr.strip()}\n")

        scale_image(out_file, opts)

        # The carbon-now CLI hits the web site, so don't hammer it.
        print("(pause)")
        time.sleep(randint(4, 9))  # noqa: S311

    print("\nRun finished.\n")


def main():
    # Run once to start.
    run_carbon()
    # Watch for changes.
    try:
        print(f"\nWatching for changes in '{code_dir}'\n")
        for changes in watch(code_dir, debounce=1500):
            print(f"\nchanges: {changes}\n")
            run_carbon()
            print("\nPress Ctrl-C to stop.\n")
    except KeyboardInterrupt:
        print("\nStopped.\n")


if __name__ == "__main__":
    main()
