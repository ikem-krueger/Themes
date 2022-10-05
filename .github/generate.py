#!/usr/bin/python3

import os
import json
import subprocess
from datetime import datetime
from urllib.parse import quote as _quote

from string import Template

from defs import (
    from_src,
    THEME_DIR,
    RELEASE_DIR,
    FEATURED_ORDERING,
    REMIXED_ORDERING,
    CUSTOM_ORDERING)

from utils import get_files, get_ordering, get_subdirs
from validation import validate_theme

README_PATH = from_src("../README.md")
README_TEMPLATE = from_src("template/README.template.md")
GRID_TEMPLATE = from_src("template/grid.template.html")
ITEM_TEMPLATE = from_src("template/item.template.html")

BGM_ICON_URL = "https://user-images.githubusercontent.com/44569252/194010780-d3659ecd-7348-4e44-a81d-06708a4e9734.png"

COLUMNS = 3

urlencode = lambda s: _quote(s, safe="/?&=_-")


def main():
    if not os.path.exists(RELEASE_DIR):
        print("No themes released")
        return

    print("Generating README...")

    released_themes = [
        os.path.splitext(file)[0]
        for file in get_files(RELEASE_DIR, "zip")]
    is_released = lambda theme: theme in released_themes

    featured = list(filter(is_released, get_ordering(FEATURED_ORDERING)))
    custom = list(filter(is_released, get_ordering(CUSTOM_ORDERING)))
    remixed = list(filter(is_released, get_ordering(REMIXED_ORDERING)))

    featured.reverse()
    custom.reverse()
    remixed.reverse()

    values = {
        "FEATURED_THEMES": generate_table_grid(featured),
        "CUSTOM_THEMES": generate_table_grid(custom),
        "REMIXED_THEMES": generate_table_grid(remixed),
    }

    with open(README_TEMPLATE, "r", encoding="utf-8") as infile:
        template = Template(infile.read())

    buffer = ("<!--" + ("!" * 56) + "\n" + ("\n" * 20) + "DO NOT EDIT THIS FILE!\n\n\nTHIS DOCUMENT WAS AUTOMATICALLY GENERATED\nRun the script `.github/generate.py` to remake this page.\n" + ("\n" * 20) + ("!" * 57) + "-->\n\n")

    buffer += template.substitute(values)

    with open(README_PATH, "w+", encoding="utf-8") as outfile:
        outfile.write(buffer)

    print("Done")


def generate_table_grid(themes) -> str:
    buffer = ""

    for i, theme in enumerate(themes):
        if i > 0 and i % COLUMNS == 0:
            buffer += "</tr><tr>\n"
        buffer += generate_item(theme)

    with open(GRID_TEMPLATE, "r", encoding="utf-8") as file:
        template = Template(file.read())

    return template.substitute({"GRID_ITEMS": buffer}) + "\n"


def generate_item(theme: str) -> str:
    dir_path = os.path.join(THEME_DIR, theme)
    is_valid, has_subdirs = validate_theme(dir_path)

    if not is_valid:
        print(f"  invalid theme: {theme}")
        return ""

    title = ""
    name_split = theme.split(" by ", maxsplit=1)
    name = name_split[0]
    author = name_split[1] if len(name_split) > 1 else ""

    if not has_subdirs:
        with open(os.path.join(dir_path, "config.json"), "r", encoding="utf-8") as infile:
            config = json.load(infile)
        if "name" in config:
            name = config["name"]
        if "author" in config:
            author = config["author"]
        if "description" in config:
            title = config["description"]

    if not title:
        title = f"{name} by {author}" if author else name

    theme_dir = f"themes/{theme}"
    if has_subdirs:
        theme_dir += "/" + get_subdirs(dir_path)[0]

    preview_url = f"{urlencode(theme_dir)}/preview.png?raw=true"
    release_url = f"release/{theme}.zip?raw=true"

    git_result = subprocess.run(
        ["git", "log", "-1", "--pretty=%cI", dir_path],
        stdout=subprocess.PIPE, check=True)
    updated = datetime.fromisoformat(git_result.stdout.decode('utf-8').strip())

    bgm_path = from_src(f"../{theme_dir}/sound/bgm.mp3")
    has_bgm = os.path.isfile(bgm_path)

    item = {
        "NAME": name,
        "AUTHOR": author or "&nbsp;",
        "TITLE": title,
        "HAS_BGM": f" &nbsp; <img src=\"{BGM_ICON_URL}\" width=\"16\" title=\"Custom background music\">" if has_bgm else "",
        "UPDATED": updated.strftime("%Y-%m-%d"),
        "PREVIEW_URL": preview_url,
        "RELEASE_URL": release_url,
    }

    with open(ITEM_TEMPLATE, "r", encoding="utf-8") as file:
        template = Template(file.read())

    return template.substitute(item) + "\n"


if __name__ == "__main__":
    main()
