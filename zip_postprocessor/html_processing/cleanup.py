import re


def remove_google_redirects(html_content):
    return re.sub(
        r'https?://www\.google\.com/url\?q=([^&]+)&[^"]+',
        lambda m: m.group(1),
        html_content
    )
