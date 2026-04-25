"""Tests for E2E and corpus utilities."""


def test_smoke_test_script_structure():
    """Test that smoke test script exists and is importable."""
    import scripts.smoke_test_p0 as smoke
    assert hasattr(smoke, 'test_p0_evidence_workflow')
    assert hasattr(smoke, 'test_p0_artifact_coverage_workflow')
    assert hasattr(smoke, 'run_p0_smoke_suite')


def test_corpus_executor_available():
    """Test that corpus executor is available."""
    from app.core.corpus_executor import CorpusSelector, PipelineExecutor
    assert callable(CorpusSelector)
    assert callable(PipelineExecutor)


def test_corpus_selector_init():
    """Test CorpusSelector initialization."""
    from app.core.corpus_executor import CorpusSelector
    from pathlib import Path
    # Use temp directory to avoid permission issues
    selector = CorpusSelector(Path("."))
    assert selector.data_dir is not None


def test_pipeline_executor_stages():
    """Test PipelineExecutor has all pipeline stages."""
    from app.core.corpus_executor import PipelineExecutor
    executor = PipelineExecutor()
    stages = ['run_full_discovery', 'run_fetch_pipeline', 'run_normalization', 
              'run_extraction', 'run_scoring', 'run_full_pipeline']
    for stage in stages:
        assert hasattr(executor, stage)
