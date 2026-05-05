"""Run a single Cramer-Lundberg simulation from the command line."""

from __future__ import annotations

import argparse

from cl_model import CramerLundbergModel


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for model parameters."""

    parser = argparse.ArgumentParser(
        description="Cramer-Lundberg ruin simulation with inverse sampling."
    )
    parser.add_argument("--u", type=float, default=10_000.0, help="Initial capital")
    parser.add_argument("--c", type=float, default=500.0, help="Premium rate")
    parser.add_argument(
        "--lambda-rate",
        type=float,
        default=1.0,
        help="Poisson intensity (lambda)",
        dest="lambda_rate",
    )
    parser.add_argument(
        "--mu-claim",
        type=float,
        default=200.0,
        help="Mean claim size (mu)",
        dest="mu_claim",
    )
    parser.add_argument("--T", type=float, default=50.0, help="Time horizon")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--trace",
        type=int,
        default=10,
        help="Number of claim events to print in the trace log",
    )
    parser.add_argument(
        "--no-plot", action="store_true", help="Skip plotting the surplus path"
    )
    return parser


def main() -> None:
    """Entry point for a single-path simulation and visualization."""

    parser = build_parser()
    args = parser.parse_args()

    model = CramerLundbergModel(
        u=args.u,
        c=args.c,
        lambda_rate=args.lambda_rate,
        mu_claim=args.mu_claim,
        T=args.T,
        seed=args.seed,
    )

    result = model.simulate()
    model.print_trace(result, limit=args.trace)

    print("\nSummary")
    print(f"Events simulated: {len(result.events)}")
    if result.ruined:
        print(f"Ruin time: {result.ruin_time:.6f}")
    else:
        print("No ruin before horizon.")

    if not args.no_plot:
        model.plot_surplus(result)


if __name__ == "__main__":
    main()
