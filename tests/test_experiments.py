import unittest

from mmsim.experiments import paired_statistics, run_experiment, strategy_statistics


def example_results(differences):
    results = []
    for difference in differences:
        results.append({"fixed": {"final_pnl": 0, "mean_absolute_inventory": 2, "trades": 3},
                        "adjusted": {"final_pnl": difference, "mean_absolute_inventory": 1, "trades": 2}})
    return results


class ExperimentTests(unittest.TestCase):
    def test_zero_adjustment_matches_in_every_scenario(self):
        results = run_experiment(n_runs=30, n_steps=10, skew_pence_per_share=0)
        for result in results:
            self.assertEqual(result["fixed"], result["adjusted"])
        paired = paired_statistics(results)
        self.assertEqual(paired["mean_pnl_difference"], 0)
        self.assertEqual(paired["approx_95_mean_interval"], (0, 0))
        self.assertEqual(paired["tie_fraction"], 1)

    def test_reproducible_scenarios_and_fixed_control(self):
        first = run_experiment(n_runs=4, n_steps=20)
        self.assertEqual(first, run_experiment(n_runs=4, n_steps=20))
        changed = run_experiment(n_runs=4, n_steps=20, skew_pence_per_share=0)
        for a, b in zip(first, changed):
            self.assertEqual(a["price_seed"], b["price_seed"])
            self.assertEqual(a["customer_seed"], b["customer_seed"])
            self.assertEqual(a["fixed"], b["fixed"])

    def test_known_outcome_summary(self):
        results = example_results([-100, 0, 100])
        stats = strategy_statistics(results, "adjusted")
        self.assertEqual(stats["mean_pnl"], 0)
        self.assertEqual(stats["pnl_standard_deviation"], 100)
        self.assertAlmostEqual(stats["loss_fraction"], 1 / 3)
        self.assertEqual(stats["worst_tail_mean_pnl"], -100)
        self.assertEqual(stats["mean_absolute_inventory"], 1)

    def test_paired_interval_describes_mean_difference(self):
        paired = paired_statistics(example_results([100] * 30))
        self.assertEqual(paired["approx_95_mean_interval"], (100, 100))
        self.assertEqual(paired["adjusted_win_fraction"], 1)
        self.assertEqual(paired["tie_fraction"], 0)
        small = paired_statistics(example_results([-100, 0, 100]))
        self.assertIsNone(small["approx_95_mean_interval"])
        self.assertAlmostEqual(small["standard_error"], 100 / (3 ** 0.5))

    def test_worst_tail_uses_correct_number_of_runs(self):
        stats = strategy_statistics(example_results(list(range(40))), "adjusted")
        self.assertEqual(stats["worst_tail_count"], 2)
        self.assertEqual(stats["worst_tail_mean_pnl"], 0.5)

    def test_invalid_experiment_sizes_fail(self):
        for settings in ({"n_runs": 1}, {"n_steps": 0}, {"skew_pence_per_share": -1}):
            with self.assertRaises(ValueError):
                run_experiment(**settings)


if __name__ == "__main__":
    unittest.main()
