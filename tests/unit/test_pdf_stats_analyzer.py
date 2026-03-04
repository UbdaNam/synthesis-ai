from pathlib import Path

from synthesis_ai.triage.pdf_stats_analyzer import PDFStatsAnalyzer


def test_pdf_stats_analyzer_metrics_shapes() -> None:
    # Uses the repository sample pdf if available; otherwise this test is skipped.
    sample_pdf = Path("background-checks.pdf")
    if not sample_pdf.exists():
        return
    stats = PDFStatsAnalyzer().analyze(str(sample_pdf))
    assert stats.page_count >= 1
    assert len(stats.character_count_per_page) == stats.page_count
    assert len(stats.character_density) == stats.page_count
    assert len(stats.image_area_ratio) == stats.page_count
    assert len(stats.font_metadata_presence) == stats.page_count
    assert "x_cluster_count" in stats.bounding_box_distribution
    assert "grid_alignment_score" in stats.bounding_box_distribution

