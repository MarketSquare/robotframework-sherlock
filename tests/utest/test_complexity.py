import pytest
from robot.api import get_model

from sherlock.model import KeywordStats
from .complexity_models import model_1complexity, model_2complexity, model_3complexity


class TestComplexity:
    @pytest.mark.parametrize("string_model, complexity", [
        (model_1complexity, 1),
        (model_2complexity, 3),
        (model_3complexity, 5)
    ])
    def test_complexity(self, string_model, complexity):
        model = get_model(string_model)
        kw_stat = KeywordStats(name="Dummy", node=model)
        assert kw_stat.complexity == complexity

    def test_complexity_without_model(self):
        kw_stat = KeywordStats(name="Dummy", node=None)
        assert kw_stat.complexity is None

    def test_complexity_print(self):
        model = get_model(model_1complexity)
        kw_stat = KeywordStats(name="Dummy", node=model)
        assert "Dummy | Used: 0 | Complexity: 1\n" == str(kw_stat)

    def test_complexity_without_model_print(self):
        kw_stat = KeywordStats(name="Dummy", node=None)
        assert "Dummy | Used: 0\n" == str(kw_stat)
