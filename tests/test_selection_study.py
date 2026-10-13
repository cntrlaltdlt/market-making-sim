import unittest
from studies.selection_study import choose_skew, seed_pairs, check_seed_split, aggregate_comparison


class EvaluationTests(unittest.TestCase):
    def test_selection_and_tie_rule(self):
        self.assertEqual(choose_skew({0: 10, 2: 12, 5: 12}), 2)
        self.assertEqual(choose_skew({0: -1, 2: -2}), 0)

    def test_seed_split_and_replay(self):
        self.assertEqual(seed_pairs(42, 10), seed_pairs(42, 10))
        check_seed_split([1, 2], [3, 4], 10, 10)
        with self.assertRaises(ValueError):
            check_seed_split([1], [1], 10, 10)

    def test_equal_weight_and_standard_error(self):
        def group(values):
            return [dict(fixed={'final_pnl': 0}, adjusted={'final_pnl': v}) for v in values]
        # Means 2, 6; sample variances 2, 2; equal weighted mean 4, SE sqrt(2)/2.
        result = aggregate_comparison([group([1,3]), group([5,7])])
        self.assertEqual(result['mean_pnl_difference'], 4)
        self.assertAlmostEqual(result['standard_error'], 2**0.5/2)

    def test_identical_strategies(self):
        groups = [[dict(fixed={'final_pnl': p}, adjusted={'final_pnl': p}) for p in (1,4,8)]]
        self.assertEqual(aggregate_comparison(groups)['approx_95_mean_interval'], [0,0])


if __name__ == '__main__':
    unittest.main()
