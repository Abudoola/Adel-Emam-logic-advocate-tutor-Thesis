"""
tests/test_tikz_export.py
-------------------------
Smoke tests for the TikZ exporter. We do not parse the LaTeX, just
verify the output is well-formed and contains the expected structural
elements.
"""
from logic_engine import AcademicLogicEngine
from tikz_export import export_to_tikz, _color_for_score


def _build_simple_engine():
    e = AcademicLogicEngine()
    e.add_argument("Msg_1", "root claim text", 10, "Fact")
    e.add_argument("Msg_2", "support text",     8, "Logic")
    e.add_argument("Msg_3", "attack text",      5, "Emotion")
    e.add_support("Msg_2", "Msg_1")
    e.add_direct_attack("Msg_3", "Msg_1")
    e.evaluate_semantics()
    return e


class TestExport:
    def test_empty_engine_returns_comment(self):
        e = AcademicLogicEngine()
        result = export_to_tikz(e)
        assert "%" in result
        assert r"\begin{figure}" not in result

    def test_complete_figure_environment(self):
        e = _build_simple_engine()
        result = export_to_tikz(e, debate_title="Test")
        assert r"\begin{figure}" in result
        assert r"\end{figure}" in result
        assert r"\begin{tikzpicture}" in result
        assert r"\end{tikzpicture}" in result
        assert r"\caption{" in result
        assert r"\label{" in result

    def test_all_nodes_appear(self):
        e = _build_simple_engine()
        result = export_to_tikz(e)
        for mid in ("Msg1", "Msg2", "Msg3"):
            assert mid in result, f"Missing node {mid} in output"

    def test_attack_and_support_edges_distinct(self):
        e = _build_simple_engine()
        result = export_to_tikz(e)
        assert r"\draw[att]" in result
        assert r"\draw[sup]" in result

    def test_special_chars_in_text_are_escaped(self):
        e = AcademicLogicEngine()
        e.add_argument("Msg_1", "100% sure & true_fact", 10, "Fact")
        e.evaluate_semantics()
        result = export_to_tikz(e, include_text=True)
        # Make sure none of these would break LaTeX compile
        assert r"\%" in result
        assert r"\&" in result
        assert r"\_" in result


class TestColorMapping:
    def test_color_zero_is_red(self):
        c = _color_for_score(0.0)
        assert "red" in c

    def test_color_one_is_green(self):
        c = _color_for_score(1.0)
        assert "green" in c

    def test_color_half_is_yellow(self):
        c = _color_for_score(0.5)
        assert "yellow" in c
