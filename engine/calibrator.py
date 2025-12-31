"""
SCORPION Baby Calibrator
========================

Calibrates, warms up, and benchmarks AI babies for optimal performance.
Ensures all babies are responding correctly before going live.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import time
import json
import logging
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-CALIBRATOR")


# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_URL = "http://localhost:11434"

BABIES = {
    "MARCUS": {
        "model": "mistral",
        "warmup_prompt": "Respond with OK if you are functioning properly.",
        "test_prompts": [
            "What is 2 + 2?",
            "Summarize: The quick brown fox jumps over the lazy dog.",
            "List 3 business strategies for growth."
        ]
    },
    "VULCAN": {
        "model": "codellama",
        "warmup_prompt": "Write a simple hello world function in Python.",
        "test_prompts": [
            "Write a function to check if a number is prime.",
            "Explain what a REST API is.",
            "Debug this code: print('hello)"
        ]
    },
    "HERMES": {
        "model": "phi",
        "warmup_prompt": "Say hello.",
        "test_prompts": [
            "What day comes after Monday?",
            "Is 10 greater than 5?",
            "Give me a one-word answer: Is the sky blue?"
        ]
    },
    "APOLLO": {
        "model": "llama2",
        "warmup_prompt": "Write a one-sentence story.",
        "test_prompts": [
            "Write a haiku about coding.",
            "Describe a sunset in one paragraph.",
            "Create a catchy slogan for a coffee shop."
        ]
    },
    "ATHENA": {
        "model": "mistral",
        "warmup_prompt": "What is the capital of France?",
        "test_prompts": [
            "Explain quantum computing in simple terms.",
            "What are the main causes of climate change?",
            "Who invented the telephone?"
        ]
    }
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CalibrationResult:
    """Result of a baby calibration test."""
    baby_name: str
    model: str
    status: str  # "pass", "fail", "timeout"
    response_time_ms: float
    response_length: int
    prompt: str
    response: str = ""
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkResult:
    """Benchmark statistics for a baby."""
    baby_name: str
    model: str
    total_tests: int
    passed: int
    failed: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    tokens_per_second: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# BABY CALIBRATOR CLASS
# =============================================================================

class BabyCalibrator:
    """
    Calibrates and benchmarks SCORPION AI babies.

    Provides:
    - Individual baby calibration
    - Warmup routines
    - Performance benchmarking
    - Collaboration testing
    - Comprehensive calibration reports
    """

    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url
        self.babies = BABIES.copy()
        self.results: Dict[str, List[CalibrationResult]] = {}
        self.benchmarks: Dict[str, BenchmarkResult] = {}

        logger.info("BabyCalibrator initialized")

    # -------------------------------------------------------------------------
    # Ollama Communication
    # -------------------------------------------------------------------------

    def _generate(self, model: str, prompt: str, timeout: int = 60) -> Dict[str, Any]:
        """Send a prompt to Ollama and get response."""
        try:
            start_time = time.time()

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=timeout
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "elapsed_ms": elapsed_ms,
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed_ms": elapsed_ms
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout", "elapsed_ms": timeout * 1000}
        except Exception as e:
            return {"success": False, "error": str(e), "elapsed_ms": 0}

    # -------------------------------------------------------------------------
    # Single Baby Operations
    # -------------------------------------------------------------------------

    def calibrate_baby(self, name: str) -> CalibrationResult:
        """Run calibration test on a single baby."""
        if name not in self.babies:
            return CalibrationResult(
                baby_name=name,
                model="unknown",
                status="fail",
                response_time_ms=0,
                response_length=0,
                prompt="",
                error=f"Unknown baby: {name}"
            )

        config = self.babies[name]
        prompt = config["warmup_prompt"]

        logger.info(f"Calibrating {name} ({config['model']})...")

        result = self._generate(config["model"], prompt)

        if result["success"]:
            calibration = CalibrationResult(
                baby_name=name,
                model=config["model"],
                status="pass",
                response_time_ms=result["elapsed_ms"],
                response_length=len(result["response"]),
                prompt=prompt,
                response=result["response"][:200]  # Truncate
            )
            logger.info(f"  ✓ {name} responding ({result['elapsed_ms']:.0f}ms)")
        else:
            calibration = CalibrationResult(
                baby_name=name,
                model=config["model"],
                status="fail",
                response_time_ms=result.get("elapsed_ms", 0),
                response_length=0,
                prompt=prompt,
                error=result.get("error", "Unknown error")
            )
            logger.warning(f"  ✗ {name} failed: {result.get('error')}")

        # Store result
        if name not in self.results:
            self.results[name] = []
        self.results[name].append(calibration)

        return calibration

    def warmup_baby(self, name: str, rounds: int = 3) -> List[CalibrationResult]:
        """Warm up a baby with multiple test prompts."""
        if name not in self.babies:
            logger.warning(f"Unknown baby: {name}")
            return []

        config = self.babies[name]
        results = []

        logger.info(f"Warming up {name} with {rounds} rounds...")

        for i in range(rounds):
            prompt = config["test_prompts"][i % len(config["test_prompts"])]
            result = self._generate(config["model"], prompt)

            calibration = CalibrationResult(
                baby_name=name,
                model=config["model"],
                status="pass" if result["success"] else "fail",
                response_time_ms=result.get("elapsed_ms", 0),
                response_length=len(result.get("response", "")),
                prompt=prompt,
                response=result.get("response", "")[:100],
                error=result.get("error", "")
            )

            results.append(calibration)

            if name not in self.results:
                self.results[name] = []
            self.results[name].append(calibration)

            logger.info(f"  Round {i+1}: {calibration.response_time_ms:.0f}ms")

        return results

    def benchmark_baby(self, name: str, iterations: int = 5) -> BenchmarkResult:
        """Run performance benchmark on a baby."""
        if name not in self.babies:
            return BenchmarkResult(
                baby_name=name,
                model="unknown",
                total_tests=0,
                passed=0,
                failed=0,
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                tokens_per_second=0
            )

        config = self.babies[name]
        times = []
        tokens = []
        passed = 0
        failed = 0

        logger.info(f"Benchmarking {name} ({iterations} iterations)...")

        for i in range(iterations):
            prompt = config["test_prompts"][i % len(config["test_prompts"])]
            result = self._generate(config["model"], prompt)

            if result["success"]:
                passed += 1
                times.append(result["elapsed_ms"])

                # Calculate tokens/sec
                if result.get("eval_duration", 0) > 0:
                    tps = result["eval_count"] / (result["eval_duration"] / 1e9)
                    tokens.append(tps)
            else:
                failed += 1

        benchmark = BenchmarkResult(
            baby_name=name,
            model=config["model"],
            total_tests=iterations,
            passed=passed,
            failed=failed,
            avg_response_time_ms=statistics.mean(times) if times else 0,
            min_response_time_ms=min(times) if times else 0,
            max_response_time_ms=max(times) if times else 0,
            tokens_per_second=statistics.mean(tokens) if tokens else 0
        )

        self.benchmarks[name] = benchmark

        logger.info(f"  Passed: {passed}/{iterations}")
        logger.info(f"  Avg time: {benchmark.avg_response_time_ms:.0f}ms")
        logger.info(f"  Tokens/sec: {benchmark.tokens_per_second:.1f}")

        return benchmark

    # -------------------------------------------------------------------------
    # Multi-Baby Operations
    # -------------------------------------------------------------------------

    def calibrate_all(self) -> Dict[str, CalibrationResult]:
        """Calibrate all babies."""
        logger.info("=" * 50)
        logger.info("  CALIBRATING ALL BABIES")
        logger.info("=" * 50)

        results = {}
        for name in self.babies:
            results[name] = self.calibrate_baby(name)

        # Summary
        passed = sum(1 for r in results.values() if r.status == "pass")
        logger.info(f"\nCalibration complete: {passed}/{len(self.babies)} babies online")

        return results

    def warmup_all(self, rounds: int = 2) -> Dict[str, List[CalibrationResult]]:
        """Warm up all babies."""
        logger.info("=" * 50)
        logger.info("  WARMING UP ALL BABIES")
        logger.info("=" * 50)

        results = {}
        for name in self.babies:
            results[name] = self.warmup_baby(name, rounds)

        return results

    def benchmark_all(self, iterations: int = 3) -> Dict[str, BenchmarkResult]:
        """Benchmark all babies."""
        logger.info("=" * 50)
        logger.info("  BENCHMARKING ALL BABIES")
        logger.info("=" * 50)

        results = {}
        for name in self.babies:
            results[name] = self.benchmark_baby(name, iterations)

        return results

    # -------------------------------------------------------------------------
    # Collaboration Testing
    # -------------------------------------------------------------------------

    def test_collaboration(self, baby1: str, baby2: str, task: str) -> Dict[str, Any]:
        """Test handoff between two babies."""
        logger.info(f"Testing collaboration: {baby1} → {baby2}")

        if baby1 not in self.babies or baby2 not in self.babies:
            return {"success": False, "error": "Invalid baby names"}

        # First baby processes
        result1 = self._generate(
            self.babies[baby1]["model"],
            f"Process this and provide a summary: {task}"
        )

        if not result1["success"]:
            return {"success": False, "error": f"{baby1} failed", "stage": 1}

        # Second baby continues
        handoff = f"Continue from: {result1['response'][:500]}"
        result2 = self._generate(
            self.babies[baby2]["model"],
            handoff
        )

        if not result2["success"]:
            return {"success": False, "error": f"{baby2} failed", "stage": 2}

        return {
            "success": True,
            "baby1_response": result1["response"][:200],
            "baby2_response": result2["response"][:200],
            "total_time_ms": result1["elapsed_ms"] + result2["elapsed_ms"]
        }

    # -------------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------------

    def calibration_report(self) -> Dict[str, Any]:
        """Generate comprehensive calibration report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "babies": {},
            "summary": {
                "total": len(self.babies),
                "calibrated": 0,
                "benchmarked": 0,
                "online": 0,
                "offline": 0
            }
        }

        for name in self.babies:
            baby_report = {
                "model": self.babies[name]["model"],
                "calibration_results": [],
                "benchmark": None,
                "status": "unknown"
            }

            # Add calibration results
            if name in self.results:
                baby_report["calibration_results"] = [
                    {
                        "status": r.status,
                        "response_time_ms": r.response_time_ms,
                        "timestamp": r.timestamp
                    }
                    for r in self.results[name][-5:]  # Last 5
                ]
                report["summary"]["calibrated"] += 1

                # Determine status from last result
                if self.results[name]:
                    last = self.results[name][-1]
                    baby_report["status"] = "online" if last.status == "pass" else "offline"
                    if last.status == "pass":
                        report["summary"]["online"] += 1
                    else:
                        report["summary"]["offline"] += 1

            # Add benchmark
            if name in self.benchmarks:
                b = self.benchmarks[name]
                baby_report["benchmark"] = {
                    "avg_response_time_ms": b.avg_response_time_ms,
                    "tokens_per_second": b.tokens_per_second,
                    "pass_rate": b.passed / b.total_tests if b.total_tests > 0 else 0
                }
                report["summary"]["benchmarked"] += 1

            report["babies"][name] = baby_report

        return report

    def print_report(self):
        """Print calibration report to console."""
        report = self.calibration_report()

        print("\n" + "=" * 60)
        print("  SCORPION BABY CALIBRATION REPORT")
        print("=" * 60)

        for name, data in report["babies"].items():
            icon = "✓" if data["status"] == "online" else "✗"
            print(f"\n  {icon} {name} ({data['model']})")

            if data["benchmark"]:
                b = data["benchmark"]
                print(f"      Avg response: {b['avg_response_time_ms']:.0f}ms")
                print(f"      Tokens/sec: {b['tokens_per_second']:.1f}")
                print(f"      Pass rate: {b['pass_rate']*100:.0f}%")

        print("\n" + "-" * 60)
        s = report["summary"]
        print(f"  Online: {s['online']}/{s['total']} babies")
        print("=" * 60 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run calibrator from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Baby Calibrator")
    parser.add_argument("--baby", help="Specific baby to calibrate")
    parser.add_argument("--warmup", action="store_true", help="Run warmup")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    parser.add_argument("--all", action="store_true", help="Calibrate all babies")
    parser.add_argument("--report", action="store_true", help="Show report")

    args = parser.parse_args()

    calibrator = BabyCalibrator()

    if args.baby:
        if args.warmup:
            calibrator.warmup_baby(args.baby)
        elif args.benchmark:
            calibrator.benchmark_baby(args.baby)
        else:
            calibrator.calibrate_baby(args.baby)
    elif args.all:
        calibrator.calibrate_all()
        if args.warmup:
            calibrator.warmup_all()
        if args.benchmark:
            calibrator.benchmark_all()
    else:
        calibrator.calibrate_all()

    if args.report:
        calibrator.print_report()


if __name__ == "__main__":
    main()
