"""Cramer-Lundberg risk model simulation.

This module implements the compound Poisson surplus process:
U(t) = u + c t - sum_{i=1}^{N(t)} Y_i.
Inter-arrival times in a Poisson process are i.i.d. Exp(lambda), so we
sample W_i by inverse transform W_i = -ln(U)/lambda. Claim sizes are
modeled as Exp(mean=mu) and sampled as Y_i = -mu ln(U).
Ruin is detected at a claim time when U(T_n) < 0.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ClaimEvent:
    """Record a single jump of the compound Poisson process."""

    index: int
    waiting_time: float
    event_time: float
    claim_size: float
    premium_income: float
    surplus: float


@dataclass(frozen=True)
class SimulationResult:
    """Container for the embedded jump chain and ruin time."""

    events: List[ClaimEvent]
    horizon: float
    initial_capital: float
    premium_rate: float
    ruin_time: Optional[float]

    @property
    def ruined(self) -> bool:
        """Return True if ruin occurred before the horizon."""

        return self.ruin_time is not None


class CramerLundbergModel:
    """Cramer-Lundberg surplus model driven by a compound Poisson process.

    The simulation follows the theorem that Poisson inter-arrival times are
    exponential and uses inverse transform sampling to generate each waiting
    time and claim size explicitly.
    """

    def __init__(
        self,
        u: float,
        c: float,
        lambda_rate: float,
        mu_claim: float,
        T: float,
        seed: Optional[int] = None,
    ) -> None:
        if u < 0:
            raise ValueError("Initial capital u must be non-negative.")
        if c <= 0:
            raise ValueError("Premium rate c must be positive.")
        if lambda_rate <= 0:
            raise ValueError("Poisson intensity lambda_rate must be positive.")
        if mu_claim <= 0:
            raise ValueError("Mean claim size mu_claim must be positive.")
        if T <= 0:
            raise ValueError("Time horizon T must be positive.")

        self.u = float(u)
        self.c = float(c)
        self.lambda_rate = float(lambda_rate)
        self.mu_claim = float(mu_claim)
        self.T = float(T)
        self.rng = random.Random(seed)

    def _uniform_open(self) -> float:
        """Return U in (0, 1) so the logarithm stays well-defined."""

        value = self.rng.random()
        if value <= 0.0:
            return 1e-12
        return value

    def _sample_waiting_time(self) -> float:
        """Sample W_i ~ Exp(lambda) via inverse transform sampling."""

        u = self._uniform_open()
        return -math.log(u) / self.lambda_rate

    def _sample_claim_size(self) -> float:
        """Sample Y_i ~ Exp(mean=mu) via inverse transform sampling."""

        u = self._uniform_open()
        return -self.mu_claim * math.log(u)

    def simulate(self) -> SimulationResult:
        """Simulate the compound Poisson surplus path until horizon or ruin.

        The while-loop iterates over Poisson arrival epochs T_n = T_{n-1} + W_n
        and updates the surplus U(T_n) = u + c T_n - sum_{i=1}^n Y_i. Ruin is
        the first passage time when U(T_n) < 0.
        """

        time = 0.0
        total_claims = 0.0
        events: List[ClaimEvent] = []
        ruin_time: Optional[float] = None
        index = 0

        while True:
            waiting_time = self._sample_waiting_time()
            time += waiting_time
            if time > self.T:
                break

            claim = self._sample_claim_size()
            total_claims += claim
            premium_income = self.c * time
            surplus = self.u + premium_income - total_claims
            index += 1

            events.append(
                ClaimEvent(
                    index=index,
                    waiting_time=waiting_time,
                    event_time=time,
                    claim_size=claim,
                    premium_income=premium_income,
                    surplus=surplus,
                )
            )

            if surplus < 0.0:
                ruin_time = time
                break

        return SimulationResult(
            events=events,
            horizon=self.T,
            initial_capital=self.u,
            premium_rate=self.c,
            ruin_time=ruin_time,
        )

    def print_trace(self, result: SimulationResult, limit: int = 10) -> None:
        """Print a trace table for the first claim events in the jump chain."""

        header = (
            f"{'i':>3} | {'W_i':>12} | {'T_i':>12} | {'Y_i':>12} | "
            f"{'c*T_i':>12} | {'U(T_i)':>12}"
        )
        print(header)
        print("-" * len(header))

        for event in result.events[:limit]:
            print(
                f"{event.index:>3d} | "
                f"{event.waiting_time:>12.6f} | "
                f"{event.event_time:>12.6f} | "
                f"{event.claim_size:>12.6f} | "
                f"{event.premium_income:>12.6f} | "
                f"{event.surplus:>12.6f}"
            )

    def _build_step_path(
        self, result: SimulationResult
    ) -> Tuple[List[float], List[float]]:
        """Build the embedded surplus path U(T_n) as a step function."""

        times = [0.0]
        values = [result.initial_capital]

        for event in result.events:
            times.append(event.event_time)
            values.append(event.surplus)

        end_time = result.ruin_time if result.ruined else result.horizon
        if times[-1] < end_time:
            times.append(end_time)
            values.append(values[-1])

        return times, values

    def plot_surplus(self, result: SimulationResult, title: str | None = None) -> None:
        """Plot the surplus path as a step function with the ruin boundary."""

        import matplotlib.pyplot as plt

        times, values = self._build_step_path(result)
        fig, ax = plt.subplots()
        ax.step(times, values, where="post", label="U(t)")
        ax.axhline(0.0, color="red", linestyle="--", label="Ruin boundary")

        ax.set_xlabel("Time t")
        ax.set_ylabel("Surplus U(t)")
        ax.set_title(title or "Cramer-Lundberg Surplus Path")
        ax.legend()
        ax.grid(True, linestyle=":", linewidth=0.5)

        plt.show()
