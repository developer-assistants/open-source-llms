import unittest

import llm_advisor


class TestLlmAdvisor(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = llm_advisor.load_dataset()
        self.models = self.dataset["models"]

    def test_dataset_validates_cleanly(self) -> None:
        errors = llm_advisor.validate_dataset()
        self.assertEqual(errors, [])

    def test_minimum_model_count(self) -> None:
        self.assertGreaterEqual(len(self.models), 25)

    def test_vram_filter_24gb(self) -> None:
        fits = llm_advisor.filter_models(self.models, max_vram=24, precision="q4")
        self.assertTrue(len(fits) >= 10)
        for model in fits:
            self.assertLessEqual(model["vram_q4_gb"], 24)

    def test_permissive_license_filter(self) -> None:
        permissive = llm_advisor.filter_models(self.models, license_tier="permissive-oss")
        self.assertTrue(len(permissive) >= 12)
        for model in permissive:
            self.assertEqual(model["license_tier"], "permissive-oss")

    def test_recommend_coding_24gb(self) -> None:
        recs = llm_advisor.recommend_models(
            self.models,
            vram=24,
            task="coding",
            permissive_only=True,
        )
        self.assertTrue(len(recs) >= 3)
        self.assertTrue(all(m["vram_q4_gb"] <= 24 for m in recs))
        self.assertTrue(all(m["license_tier"] == "permissive-oss" for m in recs))

    def test_open_data_filter(self) -> None:
        open_data = llm_advisor.filter_models(self.models, open_data_only=True)
        ids = {m["id"] for m in open_data}
        self.assertIn("olmo-2-32b", ids)


if __name__ == "__main__":
    unittest.main()
