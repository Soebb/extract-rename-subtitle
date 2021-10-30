import pathlib
import re
import shlex
import subprocess
from typing import Any, Optional, TypedDict

from subtitle_utils import (
    get_video_by_ep_collection_with_glob_and_pattern,
    get_video_collection_with_glob,
    prompt_for_user_confirmation,
    simple_ep_pattern,
)


class ExtractionMetadata(TypedDict, total=False):
    origin_video_glob: str  # Mandatory. Used to collect videos to extract subtitles from.
    sub_lang_by_track_collection: dict[
        int, str
    ]  # Currently mandatory. Specified stream track should contain extractable subtitle stream. The string value (of the dict) will be used as extracted subtitle's language tag.
    target_video_glob: str  # Optional. If supplied, extracted subtitles will be renamed after another series of videos. If not supplied, origin_video_ep_pattern and target_video_ep_pattern will be ignored and extracted subtitles will be renamed after the original videos.
    origin_video_ep_pattern: str  # Optional. Only used when targeting another series of videos to identify the episode info from the original video. (Default: simple_ep_pattern)
    target_video_ep_pattern: str  # Optional. Only used when targeting another series of videos to identify the episode info from the targeting video. (Default: simple_ep_pattern)


def extract_subtitles(
    origin_video_collection: tuple[pathlib.Path, ...],
    sub_lang_by_track_collection: dict[int, str],
    target_video_by_ep_collection: Optional[dict[str, pathlib.Path]] = None,
    origin_video_ep_pattern: re.Pattern[str] = simple_ep_pattern,
) -> None:
    def _get_sub_stem() -> str:
        if target_video_by_ep_collection:
            m = origin_video_ep_pattern.match(origin_video.stem)
            if m:
                return target_video_by_ep_collection[m[1]].stem
        return origin_video.stem

    pending_subtitle_extraction: list[tuple[str, ...]] = []
    for origin_video in origin_video_collection:
        for sub_lang, sub_track in sub_track_by_lang_collection.items():
            if sub_track is None:
                continue
            for sub_format in sub_format_collection:
                sub_name = f"{_get_sub_stem()}.{sub_lang}.{sub_format}"
                cmd = (
                    "ffmpeg",
                    "-n",
                    "-i",
                    str(origin_video),
                    "-map",
                    f":{sub_track}",
                    "-c",
                    "copy",
                    sub_name,
                )
                print(shlex.join(cmd))
                pending_subtitle_extraction.append(cmd)
    if prompt_for_user_confirmation("Start subtitle extraction?"):
        for cmd in pending_subtitle_extraction:
            subprocess.run(cmd)


def extract_fonts(video_collection: tuple[pathlib.Path, ...]) -> None:
    if not video_collection:
        return
    pending_font_extraction: list[tuple[str, ...]] = []
    font_dir = None
    for video in video_collection:
        if font_dir is None:
            font_dir = video.with_name(f"fonts-{video.stem}")
        # When extracting we will change to another working directory for ffmpeg to put all attachment into one folder. So we have to resolve the absolute path here.
        cmd = (
            "ffmpeg",
            "-dump_attachment:t",
            "",
            "-n",
            "-i",
            str(video.resolve()),
        )
        print(shlex.join(cmd))
        pending_font_extraction.append(cmd)
    assert isinstance(font_dir, pathlib.Path)
    if prompt_for_user_confirmation(f'Extract font to folder "{font_dir}?"'):
        if not font_dir.is_dir():
            font_dir.mkdir()  # This might raise a FileExistsError by design.
            # User should then take care of the existing file and re-run the script.
        for cmd in pending_font_extraction:
            subprocess.run(cmd, cwd=font_dir)


if __name__ == "__main__":
    # Read command line argument(s)
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract softsubs from a series of videos."
        ' Look at the globs / patterns / track information etc in a file named "subtitle-utils-patterns.json" to determine from which videos to extract and to what subtitle file name to write.'
        " Patterns are used to extract episode info from input videos and optionally match output subtitles to output videos names."
        " A template JSON file will be created in the working_directory if not exist and opened for editing.",
    )
    parser.add_argument(
        "video_directory",
        nargs="?",
        default=pathlib.Path(),
        help='The directory containing source videos and "subtitle-utils-patterns.json", also the place to put extracted subtitles. (Default: current working directory)',
    )
    args = parser.parse_args()

    # Read metadata
    metadata: ExtractionMetadata = {
        "origin_video_glob": "*.mkv",
        "sub_lang_by_track_collection": {1: "ja", 2: "zh-Hans", 3: "zh-Hant", 4: "eng"},
        "target_video_glob": "*.mp4",
        "origin_video_ep_pattern": r".*\s(\d{2})\s.*",
        "target_video_ep_pattern": r".*\s(\d{2})\s.*",
    }

    # Process
    extraction_args: dict[str, Any] = {}
    try:
        origin_video_collection = get_video_collection_with_glob(
            metadata["origin_video_glob"], args.video_directory
        )
        extraction_args["origin_video_collection"] = origin_video_collection
        extraction_args["sub_lang_by_track_collection"] = metadata[
            "sub_lang_by_track_collection"
        ]
    except KeyError:
        raise
    if "target_video_glob" in metadata:
        target_video_ep_pattern = (
            re.compile(metadata["target_video_ep_pattern"])
            if "target_video_ep_pattern" in metadata
            else simple_ep_pattern
        )
        origin_video_ep_pattern = (
            re.compile(metadata["origin_video_ep_pattern"])
            if "origin_video_ep_pattern" in metadata
            else simple_ep_pattern
        )
        extraction_args[
            "target_video_by_ep_collection"
        ] = get_video_by_ep_collection_with_glob_and_pattern(
            metadata["target_video_glob"], target_video_ep_pattern
        )
        extraction_args["origin_video_ep_pattern"] = origin_video_collection
    extract_subtitles(**extraction_args)
    extract_fonts(origin_video_collection)
