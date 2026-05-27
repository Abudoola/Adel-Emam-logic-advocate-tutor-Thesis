"""
tikz_export.py
--------------
Export the current argumentation graph as standalone LaTeX TikZ code
that can be pasted directly into the thesis as a figure.

The output is a complete `figure` environment requiring only the
TikZ package (already in 00BScMain.tex). No external dot2tex, no
Graphviz installation needed at LaTeX compile time.

Layout: a simple top-down layered layout where the root claim is at
layer 0 and every other node sits in a layer one greater than the
node it targets. Within a layer nodes are spaced evenly.

Colour: nodes are filled with a colour interpolated from red (s=0)
through yellow (s=0.5) to green (s=1), exactly matching the colour
scheme in the live Streamlit UI. Edge colour distinguishes attacks
(red) from supports (blue).
"""
from __future__ import annotations
from typing import Dict, List


def _assign_layers(engine) -> Dict[str, int]:
    """BFS-style layered layout. Root sits at layer 0, every other
    node sits one layer deeper than the node it targets."""
    layers: Dict[str, int] = {}
    if not engine.nodes:
        return layers

    root = next(iter(engine.nodes))  # Msg_1 by convention
    layers[root] = 0

    # Build a map: target -> list of (source) for both attack and support
    incoming: Dict[str, List[str]] = {n: [] for n in engine.nodes}
    for src, tgt in engine.attacks:
        incoming.setdefault(tgt, []).append(src)
    for src, tgt in engine.supports:
        incoming.setdefault(tgt, []).append(src)

    # BFS outward from root
    frontier = [root]
    visited = {root}
    while frontier:
        next_frontier = []
        for node in frontier:
            for src in incoming.get(node, []):
                if src not in visited:
                    layers[src] = layers[node] + 1
                    visited.add(src)
                    next_frontier.append(src)
        frontier = next_frontier

    # Any orphans (disconnected components) at the bottom
    max_layer = max(layers.values()) if layers else 0
    for mid in engine.nodes:
        if mid not in layers:
            layers[mid] = max_layer + 1

    return layers


def _color_for_score(score: float) -> str:
    """Return an `xcolor`-mixable colour expression for a given score."""
    # Interpolate red(0) → yellow(0.5) → green(1)
    if score >= 0.5:
        # blend yellow to green
        t = (score - 0.5) * 2.0
        # green!Xfill where X is 30..70 looks balanced in print
        pct = int(30 + 40 * t)
        return f"green!{pct}!yellow"
    else:
        t = score * 2.0
        pct = int(30 + 40 * (1 - t))
        return f"red!{pct}!yellow"


def _escape(text: str) -> str:
    """Make a string safe for LaTeX."""
    return (text.replace("\\", r"\textbackslash{}")
                 .replace("_", r"\_")
                 .replace("%", r"\%")
                 .replace("&", r"\&")
                 .replace("#", r"\#")
                 .replace("$", r"\$")
                 .replace("{", r"\{")
                 .replace("}", r"\}")
                 .replace("~", r"\textasciitilde{}")
                 .replace("^", r"\textasciicircum{}"))


def export_to_tikz(engine, debate_title: str = "Debate",
                   label: str = "fig:debate-graph",
                   include_text: bool = False,
                   horizontal_spacing: float = 3.0,
                   vertical_spacing: float = 2.0) -> str:
    """
    Build a complete LaTeX figure environment showing the current
    argumentation graph.

    include_text=False shows only Msg_X labels with value tag and score
    (suitable for figures whose caption explains what each node says).
    include_text=True embeds the short argument text inside each node
    (suitable for self-contained figures).
    """
    if not engine.nodes:
        return "% (No arguments in the graph yet — nothing to export.)\n"

    layers = _assign_layers(engine)
    # Group nodes by layer
    by_layer: Dict[int, List[str]] = {}
    for mid, layer in layers.items():
        by_layer.setdefault(layer, []).append(mid)

    # Sort each layer alphabetically for stable output
    for layer in by_layer:
        by_layer[layer].sort()

    lines: List[str] = []
    lines.append(r"\begin{figure}[h]")
    lines.append(r"\centering")
    lines.append(r"\begin{tikzpicture}[")
    lines.append(r"    every node/.style={font=\small},")
    lines.append(r"    arg/.style={circle, draw, minimum size=1.6cm, "
                 r"align=center, inner sep=2pt},")
    lines.append(r"    att/.style={->, >=stealth, red!70!black, thick},")
    lines.append(r"    sup/.style={->, >=stealth, blue!70!black, "
                 r"thick, dashed},")
    lines.append(r"]")

    # Place nodes by absolute coordinates
    max_layer = max(by_layer)
    for layer in sorted(by_layer):
        row = by_layer[layer]
        n = len(row)
        # Center the row horizontally around x=0
        for idx, mid in enumerate(row):
            x = (idx - (n - 1) / 2.0) * horizontal_spacing
            y = -layer * vertical_spacing  # top-down
            score = engine.scores.get(mid, 1.0)
            score_pct = int(score * 100)
            fill = _color_for_score(score)
            value_tag = engine.nodes[mid].get("value_tag", "Logic")
            tex_id = mid.replace("_", "")
            if include_text:
                text = engine.nodes[mid]["text"]
                if len(text) > 30:
                    text = text[:27] + "..."
                node_label = (f"{{\\scriptsize\\textbf{{{_escape(mid)}}}\\\\"
                              f"{_escape(text)}\\\\"
                              f"\\tiny [{value_tag}, {score_pct}\\%]}}")
            else:
                node_label = (f"{{\\textbf{{{_escape(mid)}}}\\\\"
                              f"\\tiny [{value_tag}, {score_pct}\\%]}}")
            lines.append(f"\\node[arg, fill={fill}] ({tex_id}) "
                         f"at ({x:+.2f}, {y:+.2f}) {node_label};")

    lines.append("")

    # Draw edges
    for src, tgt in engine.attacks:
        src_id = src.replace("_", "")
        tgt_id = tgt.replace("_", "")
        lines.append(f"\\draw[att] ({src_id}) -- ({tgt_id}) "
                     f"node[midway, sloped, above, font=\\tiny] "
                     f"{{$\\bigotimes$}};")
    for src, tgt in engine.supports:
        src_id = src.replace("_", "")
        tgt_id = tgt.replace("_", "")
        lines.append(f"\\draw[sup] ({src_id}) -- ({tgt_id}) "
                     f"node[midway, sloped, above, font=\\tiny] "
                     f"{{$\\bigoplus$}};")

    lines.append(r"\end{tikzpicture}")
    lines.append(f"\\caption{{Argumentation graph for the debate "
                 f"\"{_escape(debate_title)}\". "
                 f"Node fill colour encodes the acceptability score "
                 f"(red $\\to$ yellow $\\to$ green). "
                 f"Solid red edges are attacks, dashed blue edges are "
                 f"supports.}}")
    lines.append(f"\\label{{{label}}}")
    lines.append(r"\end{figure}")
    return "\n".join(lines) + "\n"
