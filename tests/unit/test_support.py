from synthesis_ai.triage.pdf_stats_analyzer import PDFStats


def sample_stats(text: str = "sample text", image_ratio: float = 0.1, cluster: float = 1.0) -> PDFStats:
    return PDFStats(
        character_count_per_page=[200],
        character_density=[0.003],
        image_area_ratio=[image_ratio],
        font_metadata_presence=[True],
        bounding_box_distribution={"x_cluster_count": cluster, "grid_alignment_score": 0.1},
        has_acroform=False,
        extracted_text=text,
    )


class FakeStatsAnalyzer:
    def __init__(self, stats: PDFStats) -> None:
        self._stats = stats

    def analyze(self, file_path: str) -> PDFStats:
        return self._stats

