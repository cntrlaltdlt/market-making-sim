import unittest
from studies.risk_study import simultaneous_mean_interval


class RiskStudyTests(unittest.TestCase):
    def test_multiple_comparison_interval_is_wider(self):
        paired = dict(mean_pnl_difference=10, standard_error=2)
        low, high = simultaneous_mean_interval(paired)
        self.assertLess(low, 10-1.96*2)
        self.assertGreater(high, 10+1.96*2)
        self.assertAlmostEqual((low+high)/2, 10)

    def test_identical_outcomes(self):
        self.assertEqual(simultaneous_mean_interval(dict(mean_pnl_difference=0, standard_error=0)), [0,0])


if __name__ == '__main__':
    unittest.main()
