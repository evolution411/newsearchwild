import re


def get_youtube_embed_url(url):
    """
    Converts YouTube Shorts or normal YouTube URL into embeddable URL.
    """

    shorts_match = re.search(r"youtube\.com/shorts/([^?&/]+)", url)
    if shorts_match:
        video_id = shorts_match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"

    watch_match = re.search(r"youtube\.com/watch\?v=([^?&/]+)", url)
    if watch_match:
        video_id = watch_match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"

    short_url_match = re.search(r"youtu\.be/([^?&/]+)", url)
    if short_url_match:
        video_id = short_url_match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"

    return ""


def get_tiktok_embed_url(url):
    """
    TikTok embed usually works better with the original TikTok URL.
    """
    return url


def get_video_embed_url(platform, url):
    if platform == "youtube":
        return get_youtube_embed_url(url)

    if platform == "tiktok":
        return get_tiktok_embed_url(url)

    return ""