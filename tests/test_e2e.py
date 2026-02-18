"""E2E tests for run-real path"""
import pytest
import subprocess
import json
import os

@pytest.mark.e2e
def test_credit_one_run_real():
    """Test credit-one run-real path"""
    result = subprocess.run(
        ['python', 'scripts/run_real.py', 'data/sample_input.csv', '--output', 'artifacts'],
        capture_output=True,
        text=True,
        cwd='/Users/zheyuliu/.openclaw/agents/main/workspace/credit-one'
    )
    assert result.returncode == 0, f"run-real failed: {result.stderr}"
    
    # Check output files exist
    report_files = [f for f in os.listdir('/Users/zheyuliu/.openclaw/agents/main/workspace/credit-one/artifacts') if f.startswith('scoring_report_')]
    assert len(report_files) > 0, "No report file generated"
    assert len(report_files) > 0, "No report file generated"
    
    with open(f'/Users/zheyuliu/.openclaw/agents/main/workspace/credit-one/artifacts/{report_files[0]}') as f:
        report = json.load(f)
    
    assert 'run_id' in report
    assert 'version' in report
    assert 'timestamp' in report
    assert 'rows_processed' in report

@pytest.mark.e2e
def test_fct_run_real():
    """Test fct run-real path"""
    result = subprocess.run(
        ['python', 'scripts/run_real.py', 'data/sample_erp.csv', '--output', 'artifacts'],
        capture_output=True,
        text=True,
        cwd='/Users/zheyuliu/.openclaw/agents/main/workspace/fct'
    )
    assert result.returncode == 0, f"run-real failed: {result.stderr}"

@pytest.mark.e2e
def test_nlp_run_real():
    """Test nlp-factor run-real path"""
    result = subprocess.run(
        ['python', 'scripts/run_real.py', 'data/sample_news.csv', '--output', 'reports'],
        capture_output=True,
        text=True,
        cwd='/Users/zheyuliu/.openclaw/agents/main/workspace/nlp-factor'
    )
    assert result.returncode == 0, f"run-real failed: {result.stderr}"
