import base64
from html.parser import HTMLParser

from app.sync.fhir_client import fhir_get

_TEXT_CONTENT_TYPES = ("text/html", "text/plain")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self._chunks.append(stripped)

    def text(self):
        return "\n".join(self._chunks)


def _strip_html(html):
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def fetch_narrative_text(attachment_url, content_type):
    """Fetch a Binary FHIR resource and return its plain-text narrative, or None."""
    if not attachment_url or not content_type or not content_type.startswith(_TEXT_CONTENT_TYPES):
        return None

    binary = fhir_get(attachment_url)
    data_b64 = binary.get("data")
    if not data_b64:
        return None

    raw_text = base64.b64decode(data_b64).decode("utf-8", errors="replace")
    if content_type.startswith("text/html"):
        return _strip_html(raw_text)
    return raw_text
