import itertools
import pathlib
import re

simple_ep_pattern = re.compile(r".*\s(\d{2})\s.*")


def format_video_by_ep_collection_with_pattern(
    video_collection: tuple[pathlib.Path, ...],
    video_ep_pattern: re.Pattern[str] = simple_ep_pattern,
) -> dict[str, pathlib.Path]:
    video_by_ep_collection: dict[str, pathlib.Path] = {}
    for video in video_collection:
        m = video_ep_pattern.match(video.stem)
        if m:
            video_by_ep_collection[m[1]] = video
    return video_by_ep_collection


def print_video_by_ep_collection(
    video_by_ep_collection: dict[str, pathlib.Path]
) -> None:
    print("Video Ep; Video path:")
    print(*itertools.starmap("{}; {}".format, video_by_ep_collection.items()), sep="\n")


def get_video_collection_with_glob(
    video_glob: str, video_dir: pathlib.Path = pathlib.Path()
) -> tuple[pathlib.Path, ...]:
    return tuple(video_dir.glob(video_glob))


def get_video_by_ep_collection_with_glob_and_pattern(
    video_glob: str = "*.mkv",
    video_ep_pattern: re.Pattern[str] = simple_ep_pattern,
    video_dir: pathlib.Path = pathlib.Path(),
) -> dict[str, pathlib.Path]:
    video_collection = get_video_collection_with_glob(video_glob, video_dir)
    return format_video_by_ep_collection_with_pattern(
        video_collection, video_ep_pattern
    )


def prompt_for_user_confirmation(request_text: str) -> bool:
    user_input = input(request_text + " [Y/n] ")
    return user_input in ("", "Y", "y")
