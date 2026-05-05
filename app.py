"""Streamlit UI for the Cramer-Lundberg Poisson simulator."""

from __future__ import annotations

import math
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cl_model import CramerLundbergModel, SimulationResult


def init_state() -> None:
    """Initialize default parameters for the Beta example."""

    defaults = {
        "u": 20.0,
        "c": 15.0,
        "lambda_rate": 3.0,
        "beta_rate": 0.25,
        "analysis_t": 10.0,
        "threshold": 5.0,
        "sim_horizon": 10.0,
        "seed": 42,
        "trace_limit": 10,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    lambda_rate: float, beta_rate: float, threshold: float, tol: float = 1e-12
) -> float:
    """P(S > threshold) for S being compound Poisson with Exp(beta_rate) claims."""

    mean = lambda_rate
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


def main() -> None:
    """Render the Streamlit UI."""

    st.set_page_config(page_title="Cramer-Lundberg Poisson Simulator", layout="wide")
    init_state()

    st.title("Cramer-Lundberg Poisson Simulator")
    st.write(
        "Interactive Cramer-Lundberg model with inverse transform sampling and "
        "analytical outputs for the Beta insurance example."
    )

    with st.sidebar:
        st.header("Parameters")
        if st.button("Load Beta example"):
            init_state()

        st.number_input(
            "Initial capital u (million USD)",
            min_value=0.0,
            key="u",
            step=1.0,
        )
        st.number_input(
            "Premium rate c (million USD/day)",
            min_value=0.0,
            key="c",
            step=0.5,
        )
        st.number_input(
            "Poisson intensity lambda (events/day)",
            min_value=0.01,
            key="lambda_rate",
            step=0.1,
        )
        st.number_input(
            "Claim rate beta (1/million USD)",
            min_value=0.01,
            key="beta_rate",
            step=0.01,
        )
        st.number_input(
            "Analysis horizon t (days)",
            min_value=0.1,
            key="analysis_t",
            step=1.0,
        )
        st.number_input(
            "Threshold for day 2 claims (million USD)",
            min_value=0.1,
            key="threshold",
            step=0.5,
        )
        st.number_input(
            "Simulation horizon T (days)",
            min_value=0.1,
            key="sim_horizon",
            step=1.0,
        )
        st.number_input("Random seed", min_value=0, key="seed", step=1)
        st.number_input("Trace events", min_value=1, key="trace_limit", step=1)

    u = float(st.session_state["u"])
    c = float(st.session_state["c"])
    lambda_rate = float(st.session_state["lambda_rate"])
    beta_rate = float(st.session_state["beta_rate"])
    analysis_t = float(st.session_state["analysis_t"])
    threshold = float(st.session_state["threshold"])

    mean_claim = 1.0 / beta_rate
    net_profit = c > lambda_rate * mean_claim

    st.subheader("Analytical results")
    st.latex(r"W_i \sim \text{Exp}(\lambda)")
    st.latex(r"T_4 \sim \text{Erlang}(k=4, \text{ rate } \lambda)")
    st.latex(
        r"P(T_2 < 1) = 1 - e^{-\lambda} (1 + \lambda)"
    )

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

    summary_rows = [
        {"Quantity": "P(T2 < 1 day)", "Value": t2_prob},
        {"Quantity": "E[X_t]", "Value": expected_claims},
        {"Quantity": "Std[X_t]", "Value": std_claims},
        {"Quantity": "P(N1=0) * P(S2>threshold)", "Value": prob_joint},
        {"Quantity": "E[R_t]", "Value": expected_reserve},
        {"Quantity": "Var[R_t]", "Value": var_reserve},
        {"Quantity": "Ruin probability", "Value": ruin_prob},
    ]

    st.dataframe(pd.DataFrame(summary_rows), hide_index=True)

    if net_profit:
        st.caption(
            "Net profit condition holds (c > lambda * E[Y]). Adjustment "
            f"coefficient R = {adjustment:.6f}."
        )
    else:
        st.warning("Net profit condition fails; ruin probability is 1.")

    st.subheader("Simulation")
    if st.button("Run simulation"):
        model = CramerLundbergModel(
            u=u,
            c=c,
            lambda_rate=lambda_rate,
            mu_claim=mean_claim,
            T=float(st.session_state["sim_horizon"]),
            seed=int(st.session_state["seed"]),
        )
        result = model.simulate()
        trace_df = trace_dataframe(result, int(st.session_state["trace_limit"]))

        st.write("Trace log (first events)")
        st.dataframe(trace_df, hide_index=True)

        times, values = build_step_path(result)
        fig, ax = plt.subplots()
        ax.step(times, values, where="post", label="U(t)")
        ax.axhline(0.0, color="red", linestyle="--", label="Ruin boundary")
        ax.set_xlabel("Time t")
        ax.set_ylabel("Surplus U(t)")
        ax.set_title("Surplus path (step function)")
        ax.legend()
        ax.grid(True, linestyle=":", linewidth=0.5)

        st.pyplot(fig)

        if result.ruined:
            st.error(f"Ruin time: {result.ruin_time:.6f}")
        else:
            st.success("No ruin before the simulation horizon.")


if __name__ == "__main__":
    main()
