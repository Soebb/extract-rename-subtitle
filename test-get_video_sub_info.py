import json
import pathlib

from subtitle_utils import get_video_sub_info

print(
    json.dumps(
        get_video_sub_info(
            pathlib.Path(
                "/run/media/jay/Seagate Basic/my-files/Downloads/Bittorrent/[MTBB] Mushoku Tensei (BD 1080p)/[MTBB] Mushoku Tensei - 01 [B3560C7B].mkv"
            )
        ),
        indent=4,
    )
)
