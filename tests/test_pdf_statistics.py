from types import SimpleNamespace

from src.agents.triage import PDFStatsAnalyzer


class _FakePage:
    width = 100.0
    height = 200.0

    def __init__(self, chars, images, words, text):
        self.chars = chars
        self.images = images
        self._words = words
        self._text = text
        self.edges = []

    def extract_words(self, **kwargs):
        return self._words

    def extract_text(self):
        return self._text

    def find_tables(self, table_settings=None):
        return []


class _FakePDF:
    def __init__(self, pages):
        self.pages = pages
        self.doc = SimpleNamespace(catalog={})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_pdf_stats_computation(monkeypatch):
    page = _FakePage(
        chars=[{"fontname": "Arial"}] * 50,
        images=[{"x0": 0, "x1": 20, "top": 0, "bottom": 30}],
        words=[{"x0": 5, "x1": 15}, {"x0": 60, "x1": 75}],
        text="invoice balance tax",
    )

    monkeypatch.setattr("src.agents.triage.pdfplumber.open", lambda _: _FakePDF([page]))
    summary = PDFStatsAnalyzer().analyze("dummy.pdf")

    assert summary.total_pages == 1
    assert summary.total_characters == 50
    assert summary.avg_char_density > 0
    assert 0 <= summary.avg_image_ratio <= 1
    assert summary.font_metadata_presence is True
    assert isinstance(summary.layout_signals_used, dict)

