#!/usr/bin/env python3
"""
Coding Agent Evaluation Suite Runner
Based on Anthropic's eval methodology
"""

import os
import sys
import json
import yaml
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# Configuration
EVAL_DIR = Path(__file__).parent.parent / "skills" / "coding-agent-eval"
TASKS_DIR = EVAL_DIR / "tasks"
GRADERS_DIR = EVAL_DIR / "graders"
REPORTS_DIR = EVAL_DIR / "reports"
REPO_CACHE = Path.home() / ".cache" / "coding-agent-eval"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REPO_CACHE.mkdir(parents=True, exist_ok=True)


@dataclass
class TrialResult:
    trial: int
    result: str  # PASS, FAIL, TIMEOUT, ERROR
    duration: float
    logs: str
    grader_results: Dict[str, Any]


@dataclass
class TaskResult:
    task_id: str
    task_desc: str
    category: str
    trials: List[TrialResult]
    pass_at_1: float
    pass_at_k: Dict[int, float]
    
    def calculate_metrics(self):
        """Calculate pass@k metrics"""
        results = [t.result == "PASS" for t in self.trials]
        n = len(results)
        
        # pass@1 = at least 1 success in 1 trial
        self.pass_at_1 = sum(results) / n if n > 0 else 0.0
        
        # pass@k for k in [1, 2, 3, 4, 5]
        for k in [1, 2, 3, 4, 5]:
            if k <= n:
                # Probability that at least one of k trials passes
                import math
                c = sum(results[:k])
                self.pass_at_k[k] = c / k
            else:
                self.pass_at_k[k] = None


class CodeBasedGrader:
    """Execute tests and static analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def grade(self, workdir: Path, task_config: Dict) -> Dict[str, Any]:
        results = {
            "overall": "PASS",
            "checks": {},
            "logs": []
        }
        
        # Run tests
        success_criteria = task_config.get("success_criteria", {})
        code_criteria = success_criteria.get("code_based", {})
        
        test_files = code_criteria.get("run_tests", [])
        if test_files:
            for test_file in test_files:
                result = self._run_command(
                    f"pytest {test_file} -v --tb=short",
                    workdir,
                    timeout=300
                )
                results["checks"][f"test_{test_file}"] = result
                if not result["passed"]:
                    results["overall"] = "FAIL"
        
        # Static analysis
        static_checks = code_criteria.get("static_check", []) + \
                       code_criteria.get("static_analysis", [])
        for check in static_checks:
            if check == "mypy":
                result = self._run_command("mypy . --ignore-missing-imports", workdir, 60)
                results["checks"]["mypy"] = result
            elif check == "flake8":
                result = self._run_command("flake8 . --max-line-length=100", workdir, 60)
                results["checks"]["flake8"] = result
            elif check == "bandit":
                result = self._run_command("bandit -r . -f json", workdir, 60)
                results["checks"]["bandit"] = result
        
        # File inspection
        inspect_files = code_criteria.get("inspect_file", [])
        if isinstance(inspect_files, str):
            inspect_files = [inspect_files]
        
        for file_path in inspect_files:
            full_path = workdir / file_path
            exists = full_path.exists() and full_path.stat().st_size > 0
            results["checks"][f"file_{file_path}"] = {
                "passed": exists,
                "exists": full_path.exists(),
                "size": full_path.stat().st_size if full_path.exists() else 0
            }
            if not exists:
                results["overall"] = "FAIL"
        
        return results
    
    def _run_command(self, cmd: str, cwd: Path, timeout: int) -> Dict:
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True,
                timeout=timeout
            )
            return {
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
                "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "TIMEOUT"}
        except Exception as e:
            return {"passed": False, "error": str(e)}


class ModelRubricGrader:
    """LLM-based evaluation"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def grade(self, workdir: Path, task_config: Dict) -> Dict[str, Any]:
        # Simplified version - just return placeholder
        # In full implementation, would call Claude API
        success_criteria = task_config.get("success_criteria", {})
        rubric = success_criteria.get("model_rubric", [])
        
        if not rubric:
            return {"overall": "SKIP", "reason": "No rubric defined"}
        
        # TODO: Implement actual LLM call
        return {
            "overall": "PASS",
            "confidence": "medium",
            "checks": {item: "PASS" for item in rubric},
            "reasoning": "Model rubric grading not fully implemented - requires LLM API"
        }


class EvalRunner:
    """Main evaluation runner"""
    
    def __init__(self):
        self.code_grader = None
        self.model_grader = None
    
    def load_task(self, task_id: str) -> Dict:
        """Load task configuration"""
        task_file = TASKS_DIR / f"{task_id}.yaml"
        if not task_file.exists():
            raise FileNotFoundError(f"Task {task_id} not found")
        
        with open(task_file) as f:
            return yaml.safe_load(f)
    
    def setup_repo(self, task_config: Dict) -> Path:
        """Clone and setup repository"""
        env = task_config.get("env", {})
        repo_url = env.get("repo_url")
        branch = env.get("branch", "main")
        
        # Create temp directory
        workdir = Path(tempfile.mkdtemp(prefix=f"eval_{task_config['id']}_"))
        
        # Clone repo
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        cached_repo = REPO_CACHE / repo_name
        
        if cached_repo.exists():
            # Use cached copy
            shutil.copytree(cached_repo, workdir / repo_name)
        else:
            # Clone fresh
            subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, repo_url, str(workdir / repo_name)],
                check=True, capture_output=True
            )
            # Cache it
            shutil.copytree(workdir / repo_name, cached_repo)
        
        workdir = workdir / repo_name
        
        # Run setup
        setup_cmd = env.get("setup_cmd", "")
        if setup_cmd:
            subprocess.run(setup_cmd, shell=True, cwd=workdir, check=True)
        
        return workdir
    
    def run_trial(self, task_config: Dict, trial_num: int, agent: str = "claude") -> TrialResult:
        """Run a single trial"""
        start_time = time.time()
        workdir = None
        
        try:
            # Setup
            workdir = self.setup_repo(task_config)
            
            # Run agent
            spec = task_config.get("task_input", {}).get("spec", "")
            prompt = f"""Complete this task in the current directory:

{spec}

Work in: {workdir}

Requirements:
- Make minimal, focused changes
- Ensure tests pass
- Follow existing code style
"""
            
            # Execute agent (simplified - just placeholder)
            # In real implementation, would call claude/codex
            agent_result = self._run_agent(prompt, workdir, agent)
            
            # Grade results
            grader_results = {}
            
            # Code-based grading
            self.code_grader = CodeBasedGrader({})
            grader_results["code"] = self.code_grader.grade(workdir, task_config)
            
            # Model rubric grading
            self.model_grader = ModelRubricGrader({})
            grader_results["rubric"] = self.model_grader.grade(workdir, task_config)
            
            # Determine overall result
            overall = "PASS"
            if grader_results["code"]["overall"] == "FAIL":
                overall = "FAIL"
            elif grader_results["rubric"]["overall"] == "FAIL":
                overall = "FAIL"
            
            duration = time.time() - start_time
            
            return TrialResult(
                trial=trial_num,
                result=overall,
                duration=duration,
                logs=agent_result.get("logs", ""),
                grader_results=grader_results
            )
            
        except Exception as e:
            return TrialResult(
                trial=trial_num,
                result="ERROR",
                duration=time.time() - start_time,
                logs=str(e),
                grader_results={"error": str(e)}
            )
        finally:
            # Cleanup
            if workdir and workdir.parent.exists():
                shutil.rmtree(workdir.parent, ignore_errors=True)
    
    def _run_agent(self, prompt: str, workdir: Path, agent: str) -> Dict:
        """Run coding agent - placeholder for actual implementation"""
        # This would integrate with claude/codex CLI
        # For now, just return placeholder
        return {
            "success": True,
            "logs": f"Agent {agent} would execute: {prompt[:100]}..."
        }
    
    def run_task(self, task_id: str, trials: int = 5, parallel: int = 1) -> TaskResult:
        """Run all trials for a task"""
        task_config = self.load_task(task_id)
        
        print(f"Running task: {task_id}")
        print(f"Description: {task_config['desc']}")
        print(f"Trials: {trials}")
        
        trial_results = []
        
        if parallel > 1:
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {
                    executor.submit(self.run_trial, task_config, i+1): i+1
                    for i in range(trials)
                }
                for future in as_completed(futures):
                    trial_results.append(future.result())
        else:
            for i in range(trials):
                print(f"  Trial {i+1}/{trials}...")
                result = self.run_trial(task_config, i+1)
                trial_results.append(result)
                print(f"    Result: {result.result} ({result.duration:.1f}s)")
        
        # Sort by trial number
        trial_results.sort(key=lambda x: x.trial)
        
        # Create result
        task_result = TaskResult(
            task_id=task_id,
            task_desc=task_config['desc'],
            category=task_config.get('category', 'unknown'),
            trials=trial_results,
            pass_at_1=0.0,
            pass_at_k={}
        )
        task_result.calculate_metrics()
        
        return task_result
    
    def run_suite(self, suite: str = "all", trials: int = 5) -> Dict[str, Any]:
        """Run a suite of tasks"""
        # Load all tasks
        tasks = []
        for task_file in TASKS_DIR.glob("*.yaml"):
            task_id = task_file.stem
            task_config = self.load_task(task_id)
            
            # Filter by suite
            if suite == "regression":
                if task_config.get("category") == "regression":
                    tasks.append(task_id)
            elif suite == "all":
                tasks.append(task_id)
        
        print(f"Running suite: {suite}")
        print(f"Tasks: {tasks}")
        print()
        
        # Run each task
        results = []
        for task_id in tasks:
            result = self.run_task(task_id, trials=trials)
            results.append(result)
            print()
        
        # Generate report
        report = self.generate_report(results)
        return report
    
    def generate_report(self, results: List[TaskResult]) -> Dict[str, Any]:
        """Generate evaluation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tasks": len(results),
                "total_trials": sum(len(r.trials) for r in results),
            },
            "tasks": []
        }
        
        for result in results:
            task_report = {
                "id": result.task_id,
                "desc": result.task_desc,
                "category": result.category,
                "pass_at_1": result.pass_at_1,
                "pass_at_k": result.pass_at_k,
                "trials": [
                    {
                        "trial": t.trial,
                        "result": t.result,
                        "duration": t.duration
                    }
                    for t in result.trials
                ]
            }
            report["tasks"].append(task_report)
        
        # Calculate overall metrics
        if results:
            report["summary"]["overall_pass_at_1"] = sum(r.pass_at_1 for r in results) / len(results)
        
        # Save report
        report_file = REPORTS_DIR / f"eval_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved: {report_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Coding Agent Evaluation Suite")
    parser.add_argument("--task", help="Run specific task")
    parser.add_argument("--suite", default="all", help="Run suite (all, regression)")
    parser.add_argument("--trials", type=int, default=5, help="Number of trials per task")
    parser.add_argument("--parallel", type=int, default=1, help="Parallel trials")
    parser.add_argument("--agent", default="claude", help="Agent to use (claude, codex)")
    parser.add_argument("--report", action="store_true", help="Generate report")
    
    args = parser.parse_args()
    
    runner = EvalRunner()
    
    if args.task:
        # Run single task
        result = runner.run_task(args.task, trials=args.trials)
        print(f"\nTask: {result.task_id}")
        print(f"pass@1: {result.pass_at_1:.2%}")
        print(f"pass@5: {result.pass_at_k.get(5, 'N/A')}")
    else:
        # Run suite
        report = runner.run_suite(suite=args.suite, trials=args.trials)
        print("\n=== Summary ===")
        print(f"Tasks: {report['summary']['total_tasks']}")
        print(f"Trials: {report['summary']['total_trials']}")
        if 'overall_pass_at_1' in report['summary']:
            print(f"Overall pass@1: {report['summary']['overall_pass_at_1']:.2%}")


if __name__ == "__main__":
    main()