import pathlib
import shlex
import subprocess
from typing import Dict, List, Optional, Pattern, Tuple

from subtitle_utils import (
    get_video_by_ep_collection_with_glob_n_pattern,
    get_video_collection_with_glob,
    prompt_for_user_confirmation,
    simple_ep_pattern,
)


def extract_subtitles(
    origin_video_collection: Tuple[pathlib.Path, ...],
    sub_track_by_lang_collection: Dict[str, Optional[int]],
    sub_format_collection: Tuple[str, ...],
    target_video_by_ep_collection: Optional[Dict[str, pathlib.Path]] = None,
    origin_video_ep_pattern: Pattern[str] = simple_ep_pattern,
) -> None:
    def _get_sub_stem() -> str:
        if target_video_by_ep_collection:
            m = origin_video_ep_pattern.match(origin_video.stem)
            if m:
                return target_video_by_ep_collection[m[1]].stem
        return origin_video.stem

    pending_subtitle_extraction: List[Tuple[str, ...]] = []
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


def extract_fonts(video_collection: Tuple[pathlib.Path, ...]) -> None:
    if not video_collection:
        return
    pending_font_extraction: List[Tuple[str, ...]] = []
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
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract softsubs from a series of videos."
        ' Look at the globs / patterns / track information etc in a file named "subtitle-utils-patterns.json" to determine from which videos to extract and to what subtitle file name to write.'
        " A template JSON file will be created in the working_directory if not exist and opened for editing.",
    )
    parser.add_argument(
        "working_directory",
        nargs="?",
        default=pathlib.Path.cwd(),
        help="The directory containing source videos and to place extracted subtitles. (Default: current working directory)",
    )
    parser.add_argument("-r", "--rename")
    args = parser.parse_args()

    # define magic const
    {
        "origin_video_glob_collection": ["*.mkv", "*.mp4"],
        "origin_video_ep_pattern": simple_ep_pattern,
        "sub_track_by_lang_collection": {
            # "ja": None,
            "zh-Hans": 2,
            "zh-Hant": 3,
            # "zh-TW": 3,
            # "zh-HK": 4,
            # "en": 5,
        },
        "is_targeting_other_videos": True,
        "target_video_glob_collection": "*SubsPlease*Super Cub*.mkv",
        "target_video_ep_pattern" = simple_ep_pattern
    }
    sub_format_collection = ("ass",)

    # process
    origin_video_collection = get_video_collection_with_glob(origin_video_glob)
    if is_targeting_other_videos:
        target_video_by_ep_collection = get_video_by_ep_collection_with_glob_n_pattern(
            target_video_glob, target_video_ep_pattern
        )
        extract_subtitles(
            origin_video_collection,
            sub_track_by_lang_collection,
            sub_format_collection,
            target_video_by_ep_collection,
            origin_video_ep_pattern,
        )
    else:
        extract_subtitles(
            origin_video_collection, sub_track_by_lang_collection, sub_format_collection
        )
    extract_fonts(origin_video_collection)
