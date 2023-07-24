import pytest
from robot.api import get_model

from sherlock.model import KeywordStats

from .complexity_models import model_1complexity, model_3complexity, model_5complexity


class TestComplexity:
    @pytest.mark.parametrize(
        "string_model, complexity", [(model_1complexity, 1), (model_3complexity, 3), (model_5complexity, 5)]
    )
    def test_complexity(self, string_model, complexity):
        model = get_model(string_model)
        kw_stat = KeywordStats(name="Dummy", parent="Dummy", node=model)
        assert kw_stat.complexity == complexity

    def test_complexity_without_model(self):
        kw_stat = KeywordStats(name="Dummy", parent="Dummy", node=None)
        assert kw_stat.complexity is None

    def test_complexity_print(self):
        model = get_model(model_1complexity)
        kw_stat = KeywordStats(name="Dummy", parent="Dummy", node=model)
        assert "Dummy\n  Used: 0\n  Complexity: 1\n" == str(kw_stat)

    def test_complexity_without_model_print(self):
        kw_stat = KeywordStats(name="Dummy", parent="Dummy", node=None)
        assert "Dummy\n  Used: 0\n" == str(kw_stat)
