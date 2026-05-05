"""Streamlit UI for the Cramer-Lundberg Poisson simulator and dashboards."""

from __future__ import annotations

import math
import random
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cl_model import CramerLundbergModel, SimulationResult


DEFAULTS = {
    "u": 20.0,
    "c": 15.0,
    "lambda_rate": 3.0,
    "beta_rate": 0.25,
    "analysis_t": 10.0,
    "threshold": 5.0,
    "sim_horizon": 10.0,
    "seed": 42,
    "trace_limit": 10,
    "sim_count": 300,
    "path_count": 20,
    "sample_size": 1000,
}

FIG_SMALL = (5.4, 3.2)
FIG_MED = (6.4, 3.6)
FIG_WIDE = (7.2, 3.8)


def init_state() -> None:
    """Initialize default parameters for the Beta example."""

    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    """Reset all parameters to the Beta example defaults."""

    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def apply_style() -> None:
    """Inject a visual theme with custom typography and cards."""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Source+Serif+4:wght@400;600&display=swap');
        :root {
          --bg-1: #f6f1e6;
          --bg-2: #eef6ff;
          --ink: #1b2631;
          --accent: #f2994a;
          --accent-2: #2f80ed;
          --card: rgba(255, 255, 255, 0.88);
          --muted: #6b7280;
          --border: rgba(31, 41, 51, 0.08);
        }
        html, body, [class*="css"]  {
          font-family: 'Space Grotesk', sans-serif;
          color: var(--ink);
        }
        .stApp {
          background: radial-gradient(1200px circle at 20% 0%, #fff3e0 0%, #f6f1e6 42%, #eef6ff 100%);
        }
        .hero {
          padding: 1.5rem 1.5rem 1.2rem;
          border-radius: 20px;
          background: linear-gradient(120deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.75));
          border: 1px solid var(--border);
          box-shadow: 0 18px 35px rgba(27, 38, 49, 0.08);
          animation: fade-in 0.9s ease-in-out;
        }
                .hero-title {
                    font-size: 2.4rem;
                    font-weight: 700;
                    margin-bottom: 0.25rem;
                    font-family: 'Source Serif 4', serif;
                }
        .hero-sub {
          color: var(--muted);
          font-size: 1.05rem;
        }
        .card {
          padding: 1rem 1.1rem;
          border-radius: 16px;
          background: var(--card);
          border: 1px solid var(--border);
          box-shadow: 0 12px 22px rgba(27, 38, 49, 0.06);
          animation: fade-up 0.65s ease-in-out;
        }
        .tag {
          display: inline-block;
          padding: 0.25rem 0.6rem;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 600;
          letter-spacing: 0.02em;
          background: rgba(242, 153, 74, 0.16);
          color: #9a5a1b;
        }
        .muted {
          color: var(--muted);
        }
        @keyframes fade-in {
          from {opacity: 0; transform: translateY(-6px);} 
          to {opacity: 1; transform: translateY(0);} 
        }
        @keyframes fade-up {
          from {opacity: 0; transform: translateY(8px);} 
          to {opacity: 1; transform: translateY(0);} 
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inverse_exponential(rate: float, rng: random.Random) -> float:
    """Sample Exp(rate) by inverse transform using P(W > t) = exp(-rate t)."""

    u = rng.random()
    u = u if u > 0.0 else 1e-12
    return -math.log(u) / rate


def sample_waiting_times(rate: float, size: int, rng: random.Random) -> List[float]:
    """Sample Poisson waiting times from Exp(rate) using inverse transform."""

    return [inverse_exponential(rate, rng) for _ in range(size)]


def sample_claim_sizes(mean_claim: float, size: int, rng: random.Random) -> List[float]:
    """Sample Exp(mean) claims via inverse transform: Y = -mu ln(U)."""

    rate = 1.0 / mean_claim
    return [inverse_exponential(rate, rng) for _ in range(size)]


def sample_erlang(rate: float, shape: int, size: int, rng: random.Random) -> List[float]:
    """Sample Erlang by summing i.i.d. exponential waiting times."""

    samples = []
    for _ in range(size):
        total = 0.0
        for _ in range(shape):
            total += inverse_exponential(rate, rng)
        samples.append(total)
    return samples


def poisson_pmf(lam: float, k: int) -> float:
    """Poisson PMF P(N=k) with rate lam."""

    return math.exp(-lam) * (lam**k) / math.factorial(k)


def sample_poisson_counts(lam: float, size: int, rng: random.Random) -> List[int]:
    """Sample Poisson counts using inverse transform sampling."""

    samples = []
    for _ in range(size):
        u = rng.random()
        p = math.exp(-lam)
        cumulative = p
        k = 0
        while u > cumulative:
            k += 1
            p *= lam / k
            cumulative += p
        samples.append(k)
    return samples


def erlang_pdf(rate: float, shape: int, x: float) -> float:
    """Erlang PDF for shape k and rate lambda."""

    if x < 0.0:
        return 0.0
    return (rate**shape) * (x ** (shape - 1)) * math.exp(-rate * x) / math.factorial(
        shape - 1
    )


def erlang_survival(rate: float, shape: int, x: float) -> float:
    """Survival function for Erlang(shape, rate) with integer shape."""

    if x <= 0:
        return 1.0
    if shape <= 0:
        return 0.0

    term = 1.0
    series_sum = 1.0
    for k in range(1, shape):
        term *= rate * x / k
        series_sum += term

    return math.exp(-rate * x) * series_sum


def compound_poisson_tail(
    lambda_rate: float,
    beta_rate: float,
    threshold: float,
    time_window: float = 1.0,
    tol: float = 1e-12,
) -> float:
    """P(S > threshold) for compound Poisson with Exp(beta_rate) claims."""

    mean = lambda_rate * time_window
    prob_n = math.exp(-mean)
    cumulative = prob_n
    tail_prob = 0.0
    n = 0

    while True:
        if n >= 1:
            tail_prob += prob_n * erlang_survival(beta_rate, n, threshold)

        n += 1
        prob_n *= mean / n
        cumulative += prob_n

        if 1.0 - cumulative < tol or n > 500:
            break

    return tail_prob


def build_step_path(result: SimulationResult) -> Tuple[List[float], List[float]]:
    """Build the step path for U(t) from jump times in the simulation."""

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


def trace_dataframe(result: SimulationResult, limit: int) -> pd.DataFrame:
    """Convert the first claim events into a DataFrame for display."""

    rows = []
    for event in result.events[:limit]:
        rows.append(
            {
                "i": event.index,
                "W_i": event.waiting_time,
                "T_i": event.event_time,
                "Y_i": event.claim_size,
                "c*T_i": event.premium_income,
                "U(T_i)": event.surplus,
            }
        )

    return pd.DataFrame(rows)


def poisson_step_path(result: SimulationResult, horizon: float) -> Tuple[List[float], List[int]]:
    """Build N(t) step path from claim event times."""

    times = [0.0]
    counts = [0]
    for event in result.events:
        times.append(event.event_time)
        counts.append(event.index)

    if times[-1] < horizon:
        times.append(horizon)
        counts.append(counts[-1])

    return times, counts


def final_surplus(result: SimulationResult, horizon: float, premium_rate: float) -> float:
    """Compute U(T) for non-ruined paths and last surplus for ruined paths."""

    total_claims = sum(event.claim_size for event in result.events)
    if result.ruined:
        return result.events[-1].surplus if result.events else result.initial_capital
    return result.initial_capital + premium_rate * horizon - total_claims


def simulate_batch(
    count: int,
    u: float,
    c: float,
    lambda_rate: float,
    mean_claim: float,
    horizon: float,
    seed: int | None,
) -> List[SimulationResult]:
    """Run multiple simulations with distinct seeds."""

    rng = random.Random(seed)
    results: List[SimulationResult] = []
    for _ in range(count):
        sim_seed = rng.randint(1, 2_000_000_000)
        model = CramerLundbergModel(
            u=u,
            c=c,
            lambda_rate=lambda_rate,
            mu_claim=mean_claim,
            T=horizon,
            seed=sim_seed,
        )
        results.append(model.simulate())
    return results


def plot_hist_with_pdf(
    data: List[float],
    pdf_func,
    title: str,
    xlabel: str,
    color: str,
    figsize: Tuple[float, float] = FIG_SMALL,
) -> None:
    """Render a histogram with a theoretical PDF overlay."""

    if not data:
        st.info("No data to display yet.")
        return

    max_val = max(data)
    grid = [max_val * i / 100 for i in range(101)]
    pdf_vals = [pdf_func(x) for x in grid]

    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(data, bins=30, density=True, alpha=0.65, color=color)
    ax.plot(grid, pdf_vals, color="#1b2631", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density")
    ax.grid(True, linestyle=":", linewidth=0.5)
    st.pyplot(fig, use_container_width=True)


def main() -> None:
    """Render the Streamlit UI."""

    st.set_page_config(page_title="Cramer-Lundberg Poisson Simulator", layout="wide")
    init_state()
    apply_style()

    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">Cramer-Lundberg Risk Lab</div>
          <div class="hero-sub">Compound Poisson engine with analytic checks, Monte Carlo panels, and visual storytelling.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Scenario inputs")
        if st.button("Load Beta example"):
            reset_state()

        st.number_input("Initial capital u (million USD)", min_value=0.0, key="u")
        st.number_input("Premium rate c (million USD/day)", min_value=0.0, key="c")
        st.number_input(
            "Poisson intensity lambda (events/day)",
            min_value=0.01,
            key="lambda_rate",
        )
        st.number_input("Claim rate beta (1/million USD)", min_value=0.01, key="beta_rate")

        st.divider()
        st.header("Analysis targets")
        st.number_input("Analysis horizon t (days)", min_value=0.1, key="analysis_t")
        st.number_input(
            "Threshold for day 2 claims (million USD)",
            min_value=0.1,
            key="threshold",
        )

        st.divider()
        st.header("Simulation settings")
        st.number_input("Simulation horizon T (days)", min_value=0.1, key="sim_horizon")
        st.number_input("Monte Carlo paths", min_value=10, key="sim_count")
        st.number_input("Paths to plot", min_value=1, key="path_count")
        st.number_input("Samples for PDFs", min_value=100, key="sample_size")
        st.number_input("Random seed", min_value=0, key="seed")
        st.number_input("Trace events", min_value=1, key="trace_limit")

    u = float(st.session_state["u"])
    c = float(st.session_state["c"])
    lambda_rate = float(st.session_state["lambda_rate"])
    beta_rate = float(st.session_state["beta_rate"])
    analysis_t = float(st.session_state["analysis_t"])
    threshold = float(st.session_state["threshold"])
    sim_horizon = float(st.session_state["sim_horizon"])
    seed = int(st.session_state["seed"])

    mean_claim = 1.0 / beta_rate
    net_profit = c > lambda_rate * mean_claim

    t2_prob = 1.0 - math.exp(-lambda_rate) * (1.0 + lambda_rate)
    expected_claims = lambda_rate * analysis_t * mean_claim
    var_claims = lambda_rate * analysis_t * (2.0 * mean_claim**2)
    std_claims = math.sqrt(var_claims)

    expected_reserve = u + c * analysis_t - expected_claims
    var_reserve = var_claims

    prob_day1_zero = math.exp(-lambda_rate)
    prob_day2_exceed = compound_poisson_tail(lambda_rate, beta_rate, threshold)
    prob_joint = prob_day1_zero * prob_day2_exceed

    if net_profit:
        adjustment = beta_rate - lambda_rate / c
        ruin_prob = math.exp(-adjustment * u)
    else:
        adjustment = None
        ruin_prob = 1.0

    metrics = st.columns(4)
    metrics[0].metric("Mean claim (mu)", f"{mean_claim:.3f}")
    metrics[1].metric("Net profit", "Yes" if net_profit else "No")
    metrics[2].metric(
        "Adjustment R",
        f"{adjustment:.4f}" if adjustment is not None else "N/A",
    )
    metrics[3].metric("Ruin prob (analytic)", f"{ruin_prob:.4f}")

    tabs = st.tabs(["Overview", "Simulation", "Distributions", "Ruin Risk"])

    with tabs[0]:
        st.subheader("Analytical results")
        st.latex(r"W_i \sim \text{Exp}(\lambda)")
        st.latex(r"T_4 \sim \text{Erlang}(k=4, \text{ rate } \lambda)")
        st.latex(r"P(T_2 < 1) = 1 - e^{-\lambda} (1 + \lambda)")

        summary_rows = [
            {"Quantity": "P(T2 < 1 day)", "Value": t2_prob},
            {"Quantity": "E[X_t]", "Value": expected_claims},
            {"Quantity": "Std[X_t]", "Value": std_claims},
            {"Quantity": "P(N1=0) * P(S2>threshold)", "Value": prob_joint},
            {"Quantity": "E[R_t]", "Value": expected_reserve},
            {"Quantity": "Var[R_t]", "Value": var_reserve},
        ]

        st.dataframe(pd.DataFrame(summary_rows), hide_index=True)

        if net_profit:
            st.caption(
                "Net profit condition holds (c > lambda * E[Y]). "
                f"Adjustment coefficient R = {adjustment:.6f}."
            )
        else:
            st.warning("Net profit condition fails; ruin probability is 1.")

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("Cashflow at t = analysis horizon")
        fig, ax = plt.subplots(figsize=FIG_MED)
        ax.bar(
            ["Premiums", "Expected claims", "Expected reserve"],
            [c * analysis_t, expected_claims, expected_reserve],
            color=["#2f80ed", "#f2994a", "#27ae60"],
        )
        ax.set_ylabel("Million USD")
        ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Simulation lab")
        st.write("Run single-path simulation and inspect event-level traces.")

        if st.button("Run single path"):
            model = CramerLundbergModel(
                u=u,
                c=c,
                lambda_rate=lambda_rate,
                mu_claim=mean_claim,
                T=sim_horizon,
                seed=seed,
            )
            st.session_state["latest_result"] = model.simulate()

        result: SimulationResult | None = st.session_state.get("latest_result")
        if result is not None:
            trace_df = trace_dataframe(result, int(st.session_state["trace_limit"]))
            st.write("Trace log (first events)")
            st.dataframe(trace_df, hide_index=True)

            times, values = build_step_path(result)
            chart_cols = st.columns(2)
            fig, ax = plt.subplots(figsize=FIG_MED)
            ax.step(times, values, where="post", label="U(t)", linewidth=2)
            ax.axhline(0.0, color="red", linestyle="--", label="Ruin boundary")
            ax.set_xlabel("Time t")
            ax.set_ylabel("Surplus U(t)")
            ax.set_title("Surplus path (step function)")
            ax.legend()
            ax.grid(True, linestyle=":", linewidth=0.5)
            chart_cols[0].pyplot(fig, use_container_width=True)

            premiums = [0.0]
            claims = [0.0]
            times_cf = [0.0]
            for event in result.events:
                times_cf.append(event.event_time)
                premiums.append(event.premium_income)
                claims.append(claims[-1] + event.claim_size)

            end_time = result.ruin_time if result.ruined else sim_horizon
            if times_cf[-1] < end_time:
                times_cf.append(end_time)
                premiums.append(c * end_time)
                claims.append(claims[-1])

            fig, ax = plt.subplots(figsize=FIG_MED)
            ax.plot(times_cf, premiums, label="Cumulative premiums", color="#2f80ed")
            ax.plot(times_cf, claims, label="Cumulative claims", color="#f2994a")
            ax.set_xlabel("Time t")
            ax.set_ylabel("Million USD")
            ax.set_title("Cashflow decomposition")
            ax.legend()
            ax.grid(True, linestyle=":", linewidth=0.5)
            chart_cols[1].pyplot(fig, use_container_width=True)

            if result.events:
                chart_cols = st.columns(2)
                fig, ax = plt.subplots(figsize=FIG_MED)
                ax.bar(
                    [event.index for event in result.events],
                    [event.claim_size for event in result.events],
                    color="#1abc9c",
                )
                ax.set_xlabel("Event index")
                ax.set_ylabel("Claim size")
                ax.set_title("Claim sizes by event")
                ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
                chart_cols[0].pyplot(fig, use_container_width=True)

                fig, ax = plt.subplots(figsize=FIG_MED)
                nt_times, nt_counts = poisson_step_path(result, sim_horizon)
                ax.step(nt_times, nt_counts, where="post", color="#2f80ed")
                ax.set_xlabel("Time t")
                ax.set_ylabel("N(t)")
                ax.set_title("Poisson counting process N(t)")
                ax.grid(True, linestyle=":", linewidth=0.5)
                chart_cols[1].pyplot(fig, use_container_width=True)

            if result.ruined:
                st.error(f"Ruin time: {result.ruin_time:.6f}")
            else:
                st.success("No ruin before the simulation horizon.")

        st.divider()
        st.write("Multi-path preview")
        if st.button("Plot multiple paths"):
            path_count = int(st.session_state["path_count"])
            paths = simulate_batch(
                count=path_count,
                u=u,
                c=c,
                lambda_rate=lambda_rate,
                mean_claim=mean_claim,
                horizon=sim_horizon,
                seed=seed + 17,
            )
            fig, ax = plt.subplots(figsize=FIG_WIDE)
            for path in paths:
                times, values = build_step_path(path)
                ax.step(times, values, where="post", alpha=0.6, linewidth=1)
            ax.axhline(0.0, color="red", linestyle="--", linewidth=1)
            ax.set_title("Multiple surplus paths")
            ax.set_xlabel("Time t")
            ax.set_ylabel("Surplus U(t)")
            ax.grid(True, linestyle=":", linewidth=0.5)
            st.pyplot(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("Distribution diagnostics")
        rng = random.Random(seed + 7)
        sample_size = int(st.session_state["sample_size"])

        waiting_times = sample_waiting_times(lambda_rate, sample_size, rng)
        claim_sizes = sample_claim_sizes(mean_claim, sample_size, rng)
        t4_samples = sample_erlang(lambda_rate, 4, sample_size, rng)

        cols = st.columns(2)
        with cols[0]:
            plot_hist_with_pdf(
                waiting_times,
                lambda x: lambda_rate * math.exp(-lambda_rate * x),
                "Waiting times W_i",
                "Days",
                "#2f80ed",
                figsize=FIG_SMALL,
            )
            st.caption(
                f"Sample mean: {sum(waiting_times)/len(waiting_times):.4f}, "
                f"theoretical mean: {1/lambda_rate:.4f}"
            )

        with cols[1]:
            plot_hist_with_pdf(
                claim_sizes,
                lambda x: (1.0 / mean_claim) * math.exp(-x / mean_claim),
                "Claim sizes Y_i",
                "Million USD",
                "#f2994a",
                figsize=FIG_SMALL,
            )
            st.caption(
                f"Sample mean: {sum(claim_sizes)/len(claim_sizes):.4f}, "
                f"theoretical mean: {mean_claim:.4f}"
            )

        plot_hist_with_pdf(
            t4_samples,
            lambda x: erlang_pdf(lambda_rate, 4, x),
            "Event time T4 (Erlang)",
            "Days",
            "#27ae60",
            figsize=FIG_MED,
        )

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("Poisson count diagnostics")
        lam_t = lambda_rate * analysis_t
        count_samples = sample_poisson_counts(lam_t, sample_size, rng)
        max_k = max(count_samples) if count_samples else 0
        bins = list(range(0, max_k + 2))
        fig, ax = plt.subplots(figsize=FIG_MED)
        ax.hist(count_samples, bins=bins, density=True, color="#2f80ed", alpha=0.7)
        pmf_vals = [poisson_pmf(lam_t, k) for k in range(max_k + 1)]
        ax.plot(range(max_k + 1), pmf_vals, "o-", color="#1b2631")
        ax.set_xlabel(f"N(t) with t={analysis_t:.2f}")
        ax.set_ylabel("Probability")
        ax.set_title("Poisson counts vs theoretical PMF")
        ax.grid(True, linestyle=":", linewidth=0.5)
        st.pyplot(fig, use_container_width=True)
        st.caption(
            f"Sample mean: {sum(count_samples)/len(count_samples):.3f}, "
            f"sample var: {pd.Series(count_samples).var():.3f}, "
            f"theory mean=var={lam_t:.3f}"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.subheader("Ruin risk Monte Carlo")
        st.write(
            "Estimate ruin probability and reserve distribution with repeated simulations."
        )
        if st.button("Run Monte Carlo"):
            sim_count = int(st.session_state["sim_count"])
            results = simulate_batch(
                count=sim_count,
                u=u,
                c=c,
                lambda_rate=lambda_rate,
                mean_claim=mean_claim,
                horizon=sim_horizon,
                seed=seed + 99,
            )
            st.session_state["mc_results"] = results

        mc_results: List[SimulationResult] | None = st.session_state.get("mc_results")
        if mc_results:
            ruin_flags = [result.ruined for result in mc_results]
            ruin_times = [result.ruin_time for result in mc_results if result.ruined]
            final_values = [
                final_surplus(result, sim_horizon, c) for result in mc_results
            ]

            empirical_ruin = sum(ruin_flags) / len(ruin_flags)
            mean_ruin_time = (
                sum(ruin_times) / len(ruin_times) if ruin_times else None
            )

            stats_cols = st.columns(3)
            stats_cols[0].metric("Empirical ruin prob", f"{empirical_ruin:.4f}")
            stats_cols[1].metric(
                "Mean ruin time",
                f"{mean_ruin_time:.4f}" if mean_ruin_time is not None else "N/A",
            )
            stats_cols[2].metric("Paths", f"{len(mc_results)}")

            chart_cols = st.columns(2)
            fig, ax = plt.subplots(figsize=FIG_MED)
            ax.hist(final_values, bins=30, color="#2f80ed", alpha=0.7)
            ax.axvline(0.0, color="red", linestyle="--")
            ax.set_title("Distribution of U(T)")
            ax.set_xlabel("Surplus")
            ax.set_ylabel("Frequency")
            ax.grid(True, linestyle=":", linewidth=0.5)
            chart_cols[0].pyplot(fig, use_container_width=True)

            if ruin_times:
                fig, ax = plt.subplots(figsize=FIG_MED)
                ax.hist(ruin_times, bins=30, color="#f2994a", alpha=0.7)
                ax.set_title("Ruin time distribution")
                ax.set_xlabel("Time")
                ax.set_ylabel("Frequency")
                ax.grid(True, linestyle=":", linewidth=0.5)
                chart_cols[1].pyplot(fig, use_container_width=True)
            else:
                chart_cols[1].info("No ruin observed in the Monte Carlo runs.")


if __name__ == "__main__":
    main()
