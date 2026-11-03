import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from citysight.data.types import CATEGORIES, CountTable, WardFeatures
from citysight.evaluation.metrics import category_ranking_metrics, ranking_metrics, regression_metrics
from citysight.evaluation.runner import challenge_split
from citysight.features.tabular import fit_encoder, transform
from citysight.models.baselines import category_month_means, predict_k5
from types import MappingProxyType
from datetime import datetime


def table(counts, wards, months):
    return CountTable(MappingProxyType(counts), tuple(wards), tuple(months), sum(counts.values()), 0,
                      datetime(2024, 1, 1), datetime(2024, 2, 1))


class MetricsTests(unittest.TestCase):
    def test_zero_actual_wape_is_null_with_reason(self):
        result = regression_metrics([0, 0], [2, 0])
        self.assertIsNone(result["wape"])
        self.assertEqual(result["wape_undefined_reason"], "zero_actual_total")
        self.assertEqual(result["mae"], 1)

    def test_hand_computed_wape_mae(self):
        result = regression_metrics([2, 4], [1, 6])
        self.assertEqual(result["wape"], 0.5)
        self.assertEqual(result["mae"], 1.5)

    def test_rank_ties_and_top_quarter_tie_break(self):
        result = ranking_metrics({"a": 1, "b": 1, "c": 0, "d": 0},
                                 {"a": 1, "b": 0, "c": 1, "d": 0})
        self.assertEqual(result["top_k"], 1)
        self.assertEqual(result["top_quarter_recall"], 1.0)

    def test_constant_rank_vector_returns_null(self):
        result = ranking_metrics({"a": 1, "b": 1}, {"a": 0, "b": 0})
        self.assertIsNone(result["spearman"])
        self.assertEqual(result["spearman_undefined_reason"], "constant_rank_vector")

    def test_ranking_averages_categories_and_excludes_undefined(self):
        actual = {"a": {"1": 1, "2": 2, "3": 3, "4": 4},
                  "b": {"1": 1, "2": 2, "3": 3, "4": 4},
                  "c": {"1": 1, "2": 1, "3": 1, "4": 1}}
        predicted = {"a": {"1": 1, "2": 2, "3": 3, "4": 4},
                     "b": {"1": 4, "2": 3, "3": 2, "4": 1},
                     "c": {"1": 1, "2": 2, "3": 3, "4": 4}}
        result = category_ranking_metrics(actual, predicted)
        self.assertAlmostEqual(result["spearman"], 0.0)
        self.assertEqual(result["spearman_undefined_categories"], ["c"])
        self.assertAlmostEqual(result["top_quarter_recall"], 1 / 3)
        self.assertEqual(result["top_k"], 1)

    def test_all_constant_categories_report_undefined_mean(self):
        values = {"a": {"1": 1, "2": 1}, "b": {"1": 2, "2": 2}}
        result = category_ranking_metrics(values, values)
        self.assertIsNone(result["spearman"])
        self.assertEqual(result["spearman_undefined_reason"], "all_categories_constant")
        self.assertEqual(result["spearman_undefined_categories"], ["a", "b"])

    def test_ranking_rejects_mismatched_category_sets(self):
        with self.assertRaises(ValueError):
            category_ranking_metrics({"a": {"1": 1}}, {"b": {"1": 1}})

    def test_reject_nonfinite_and_negative(self):
        with self.assertRaises(ValueError):
            regression_metrics([1], [math.nan])
        with self.assertRaises(ValueError):
            regression_metrics([-1], [0])


class SplitAndLeakageTests(unittest.TestCase):
    def test_challenge_is_reproducible_and_unique(self):
        wards = [f"{i:03}" for i in range(30)]
        self.assertEqual(challenge_split(wards, 5), challenge_split(list(reversed(wards)), 5))
        self.assertEqual(len(challenge_split(wards, 5)), 5)

    def test_cm_uses_only_training_wards(self):
        counts = {(w, m, c): n for w, n in (("1", 1), ("2", 3), ("9", 100))
                  for m in ("2024-01",) for c in CATEGORIES}
        ct = table(counts, ("1", "2", "9"), ("2024-01",))
        exact, _ = category_month_means(ct, ("1", "2"))
        self.assertEqual(exact[("electrical", "2024-01")], 2)

    def test_changing_heldout_labels_does_not_change_cm_training_fit(self):
        wards = ("1", "2", "9")
        counts_a = {(w, "2024-01", c): n for w, n in (("1", 1), ("2", 3), ("9", 100)) for c in CATEGORIES}
        counts_b = dict(counts_a)
        for category in CATEGORIES:
            counts_b[("9", "2024-01", category)] = 999999
        a = category_month_means(table(counts_a, wards, ("2024-01",)), ("1", "2"))[0]
        b = category_month_means(table(counts_b, wards, ("2024-01",)), ("1", "2"))[0]
        self.assertEqual(a, b)

    def test_k5_excludes_nontraining_ward(self):
        wards = ("1", "2", "3", "4", "5", "6", "9")
        counts = {(w, "2024-01", c): (1000 if w == "9" else int(w)) for w in wards for c in CATEGORIES}
        ct = table(counts, wards, ("2024-01",))
        features = {}
        for i, w in enumerate(wards):
            features[w] = WardFeatures(w, MappingProxyType({}),
                MappingProxyType({"centroid_lat": 0.0, "centroid_lon": float(i) / 100}))
        pred = predict_k5(ct, ("1", "2", "3", "4", "5", "6"), features,
                          "9", "2024-01", "electrical")
        self.assertEqual(pred, 4.0)

    def test_encoder_medians_and_unknown_zone_are_train_local(self):
        train = WardFeatures("1", MappingProxyType({"zone": "A"}), MappingProxyType({"population_2011": 10.0}))
        test = WardFeatures("2", MappingProxyType({"zone": "UNSEEN"}), MappingProxyType({"population_2011": None}))
        enc = fit_encoder([train])
        row = transform(test, "2024-01", "roads", enc)
        self.assertEqual(row[0], 10.0)
        self.assertEqual(sum(row[-1:]), 0.0)  # unseen zone is all-zero
        self.assertIn("area_sq_km", enc.all_missing)

    def test_encoder_recognizes_bbmp_zone_name(self):
        train = WardFeatures("1", MappingProxyType({"bbmp_zone_name": "East"}), MappingProxyType({"population_2011": 10.0}))
        test = WardFeatures("2", MappingProxyType({"bbmp_zone_name": "East"}), MappingProxyType({"population_2011": 20.0}))
        enc = fit_encoder([train])
        self.assertEqual(enc.zones, ("East",))
        row = transform(test, "2024-01", "roads", enc)
        self.assertEqual(row[-1], 1.0)


class SelectionRuleTests(unittest.TestCase):
    def test_hgb_selected_when_pooled_lower_and_at_least_three_fold_wins(self):
        # HGB wins 4/5 folds and pooled WAPE lower
        cm_folds = [{"wape": 0.8}, {"wape": 0.7}, {"wape": 0.7}, {"wape": 0.8}, {"wape": 0.7}]
        k5_folds = [{"wape": 0.65}, {"wape": 0.60}, {"wape": 0.62}, {"wape": 0.65}, {"wape": 0.55}]
        hgb_folds = [{"wape": 0.57}, {"wape": 0.47}, {"wape": 0.51}, {"wape": 0.49}, {"wape": 0.68}]

        # Test selection logic matching runner
        results = {
            "cm": {"status": "PASS", "pooled_wape": 0.74, "folds": cm_folds},
            "k5": {"status": "PASS", "pooled_wape": 0.62, "folds": k5_folds},
            "hgb": {"status": "PASS", "pooled_wape": 0.54, "folds": hgb_folds},
        }
        valid_baselines = [(r["pooled_wape"], name) for name, r in results.items()
                           if name in ("cm", "k5") and r["status"] == "PASS" and r["pooled_wape"] is not None]
        baseline_score, selected = min(valid_baselines, key=lambda x: (x[0], x[1] != "cm"))
        self.assertEqual(selected, "k5")

        hgb = results.get("hgb")
        wins = sum((fold.get("wape") is not None and results[selected]["folds"][i].get("wape") is not None
                    and fold["wape"] < results[selected]["folds"][i]["wape"])
                   for i, fold in enumerate(hgb["folds"]))
        self.assertEqual(wins, 4)
        if hgb["pooled_wape"] < baseline_score and wins >= 3:
            selected = "hgb"
        self.assertEqual(selected, "hgb")

    def test_hgb_rejected_if_pooled_lower_but_wins_under_three_folds(self):
        # HGB has lower pooled WAPE but only wins 2 folds
        k5_folds = [{"wape": 0.50}, {"wape": 0.50}, {"wape": 0.50}, {"wape": 0.80}, {"wape": 0.80}]
        hgb_folds = [{"wape": 0.51}, {"wape": 0.51}, {"wape": 0.51}, {"wape": 0.20}, {"wape": 0.20}]
        results = {
            "cm": {"status": "PASS", "pooled_wape": 0.70, "folds": [{"wape": 0.7}] * 5},
            "k5": {"status": "PASS", "pooled_wape": 0.62, "folds": k5_folds},
            "hgb": {"status": "PASS", "pooled_wape": 0.38, "folds": hgb_folds},
        }
        valid_baselines = [(r["pooled_wape"], name) for name, r in results.items()
                           if name in ("cm", "k5") and r["status"] == "PASS" and r["pooled_wape"] is not None]
        baseline_score, selected = min(valid_baselines, key=lambda x: (x[0], x[1] != "cm"))
        hgb = results.get("hgb")
        wins = sum((fold.get("wape") is not None and results[selected]["folds"][i].get("wape") is not None
                    and fold["wape"] < results[selected]["folds"][i]["wape"])
                   for i, fold in enumerate(hgb["folds"]))
        self.assertEqual(wins, 2)
        if hgb["pooled_wape"] < baseline_score and wins >= 3:
            selected = "hgb"
        self.assertEqual(selected, "k5")  # HGB rejected, k5 retained

    def test_baseline_tie_prefers_cm(self):
        results = {
            "cm": {"status": "PASS", "pooled_wape": 0.60, "folds": [{"wape": 0.6}] * 5},
            "k5": {"status": "PASS", "pooled_wape": 0.60, "folds": [{"wape": 0.6}] * 5},
        }
        valid_baselines = [(r["pooled_wape"], name) for name, r in results.items()
                           if name in ("cm", "k5") and r["status"] == "PASS" and r["pooled_wape"] is not None]
        baseline_score, selected = min(valid_baselines, key=lambda x: (x[0], x[1] != "cm"))
        self.assertEqual(selected, "cm")


if __name__ == "__main__":
    unittest.main()
