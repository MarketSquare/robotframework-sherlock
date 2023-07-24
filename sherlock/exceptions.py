import difflib
import re
from collections import defaultdict


class RecommendationFinder:
    def find_similar(self, name, candidates):
        norm_name = self.normalize(name)
        norm_cand = self.get_normalized_candidates(candidates)
        matches = []
        for norm in norm_name:
            matches += self.find(norm, norm_cand.keys())
        if not matches:
            return ""
        matches = self.get_original_candidates(matches, norm_cand)
        suggestion = "Did you mean:\n"
        suggestion += "\n".join(f"    {match}" for match in matches)
        return suggestion

    def find(self, name, candidates, max_matches=5):
        """Return a list of close matches to `name` from `candidates`."""
        if not name or not candidates:
            return []
        cutoff = self._calculate_cutoff(name)
        return difflib.get_close_matches(name, candidates, n=max_matches, cutoff=cutoff)

    @staticmethod
    def _calculate_cutoff(string, min_cutoff=0.5, max_cutoff=0.85, step=0.03):
        """The longer the string the bigger required cutoff."""
        cutoff = min_cutoff + len(string) * step
        return min(cutoff, max_cutoff)

    @staticmethod
    def normalize(name):
        """
        Return tuple where first element is string created from sorted words in name,
        and second element is name without `-` and `_`.
        """
        norm = re.split("[-_ ]+", name)
        return " ".join(sorted(norm)), name.replace("-", "").replace("_", "")

    @staticmethod
    def get_original_candidates(candidates, norm_candidates):
        """Map found normalized candidates to unique original candidates."""
        return sorted(list(set(c for cand in candidates for c in norm_candidates[cand])))

    def get_normalized_candidates(self, candidates):
        """
        Thanks for normalizing and sorting we can find cases like this-is, thisis, this-is1 instead of is-this.
        Normalized names form dictionary that point to original names - we're using list because several names can
        have one common normalized name.
        Different normalization methods try to imitate possible mistakes done when typing name - different order,
        missing `-` etc.
        """
        norm = defaultdict(list)
        for cand in candidates:
            for norm_cand in self.normalize(cand):
                norm[norm_cand].append(cand)
        return norm


class SherlockFatalError(ValueError):
    pass


class ConfigGeneralError(SherlockFatalError):
    pass


class InvalidReportName(ConfigGeneralError):
    def __init__(self, report, reports):
        report_names = sorted(list(reports.keys()))
        msg = (
            f"Provided report '{report}' does not exist. "
            f"Use comma separated list of values from: {','.join(report_names)}. "
        )
        similar = RecommendationFinder().find_similar(report, report_names)
        msg += similar
        super().__init__(msg)
