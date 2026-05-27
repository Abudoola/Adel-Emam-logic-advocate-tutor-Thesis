"""
views/engine_inspector.py
-------------------------
The 'Defense Mode' panel.

This panel is meant for the thesis defense and any time you need to
demonstrate the SYMBOLIC vs NEURAL separation of the system to a
viewer. It shows:

  1. Every node in the engine with its weight, value tag, and live
     acceptability score.
  2. Every attack and support edge.
  3. The engine's convergence info (how many iterations it took).
  4. The current MDP state (own status, opponent pressure, hint streak)
     and the action the policy would pick right now.
  5. A 'Why am I losing?' diagnostic that walks through the engine's
     verdict on the user's main claim.
  6. A 'What if?' sandbox that lets you mutate a node's weight or
     value tag (or delete it) and see how the verdict on the main
     claim would change, side-by-side with the real verdict.
"""
from __future__ import annotations
from typing import Dict, List

import streamlit as st

from logic_engine import AcademicLogicEngine, VALUE_WEIGHTS, VALID_VALUE_TAGS
from hint_mdp import derive_state, choose_action, policy_table


def render_inspector_panel(engine, messages, learner_side: str,
                           recent_hints: int) -> None:
    """Render the inspector. Wraps everything in a single expander."""
    with st.expander("🧪 Engine Inspector (Defense Mode)", expanded=False):
        _render_legend()
        st.divider()

        tab_nodes, tab_relations, tab_mdp, tab_diag, tab_whatif = st.tabs([
            "📦 Nodes", "🔗 Relations", "🎯 MDP State", "🩺 Diagnose",
            "🧪 What If?",
        ])

        with tab_nodes:
            _render_nodes(engine)
        with tab_relations:
            _render_relations(engine)
        with tab_mdp:
            _render_mdp(engine, messages, learner_side, recent_hints)
        with tab_diag:
            _render_diagnose(engine, messages, learner_side)
        with tab_whatif:
            _render_whatif(engine, messages)


# ----------------------------------------------------------------- Legend

def _render_legend() -> None:
    st.caption(
        "🔴 Red border = **Neural** components (LLaMA-3, Whisper).  "
        "🟡 Yellow border = **Symbolic** components (Dung framework, MDP)."
    )
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            '<div class="inspector-card inspector-symbolic">'
            '<span class="badge-symbolic">SYMBOLIC</span> '
            'AcademicLogicEngine</div>',
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            '<div class="inspector-card inspector-symbolic">'
            '<span class="badge-symbolic">SYMBOLIC</span> '
            'Hint MDP</div>',
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            '<div class="inspector-card inspector-neural">'
            '<span class="badge-neural">NEURAL</span> '
            'LLaMA-3 / Whisper</div>',
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------- Nodes

def _render_nodes(engine) -> None:
    if not engine.nodes:
        st.info("No arguments in the graph yet. Make a move first.")
        return

    info = engine.convergence_info()
    st.caption(
        f"Convergence: {info['iterations_until_stable']}/{info['max_iterations']} iterations · "
        f"{info['node_count']} nodes · {info['attack_count']} attacks · "
        f"{info['support_count']} supports"
    )

    rows = []
    for mid, n in engine.nodes.items():
        score = engine.scores.get(mid, 1.0)
        status = engine.statuses.get(mid, "OUT")
        rows.append({
            "ID":     mid,
            "Text":   (n["text"][:50] + "…") if len(n["text"]) > 50 else n["text"],
            "Value":  n.get("value_tag", "Logic"),
            "μ":      VALUE_WEIGHTS[n.get("value_tag", "Logic")],
            "Weight": n["weight"],
            "Score":  round(score, 3),
            "Status": status,
        })
    st.dataframe(rows, hide_index=True, use_container_width=True)


# ----------------------------------------------------------- Relations

def _render_relations(engine) -> None:
    if not engine.attacks and not engine.supports:
        st.info("No relations yet.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**⚔️ Attack relation $R_{att}$**")
        if engine.attacks:
            for atk, tgt in engine.attacks:
                a_score = engine.scores.get(atk, 0)
                t_score = engine.scores.get(tgt, 0)
                st.markdown(
                    f'<div class="inspector-card inspector-symbolic">'
                    f'{atk} → {tgt} '
                    f'<small>(s={a_score:.2f} attacks s={t_score:.2f})</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("(empty)")

    with c2:
        st.markdown("**🛡️ Support relation $R_{sup}$**")
        if engine.supports:
            for sup, tgt in engine.supports:
                a_score = engine.scores.get(sup, 0)
                t_score = engine.scores.get(tgt, 0)
                st.markdown(
                    f'<div class="inspector-card inspector-symbolic">'
                    f'{sup} → {tgt} '
                    f'<small>(s={a_score:.2f} supports s={t_score:.2f})</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("(empty)")


# -------------------------------------------------------------- MDP State

def _render_mdp(engine, messages, learner_side: str, recent_hints: int) -> None:
    state = derive_state(engine, messages, learner_side, recent_hints)
    action = choose_action(state)
    own, pressure, streak = state

    st.markdown(f"**Current MDP state:** `{state}`")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Own status",        own)
    with c2: st.metric("Opponent pressure", pressure)
    with c3: st.metric("Hint streak",       streak)

    st.markdown(f"**Optimal action right now:** `{action}`")
    st.caption("(This is what the hint button would request if you pressed it.)")

    with st.expander("Show full policy π* (state → action)", expanded=False):
        pol = policy_table()
        rows = [{"State": str(s), "Optimal action": a} for s, a in pol.items()]
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ------------------------------------------------------------- Diagnostic

def _render_diagnose(engine, messages, learner_side: str) -> None:
    own_msgs = [m for m in messages if m["side"] == learner_side]
    if not own_msgs:
        st.info("Make a move first to see a diagnosis.")
        return

    main_claim_id = own_msgs[0]["id"]
    diag = engine.diagnose(main_claim_id)

    st.markdown(f"**Your main claim ({diag['id']}):**")
    st.info(diag["text"])
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Value tag", diag["value_tag"])
    with c2: st.metric("Weight",    diag["weight"])
    with c3: st.metric("Score",     f"{diag['score']:.2f}")

    st.markdown(f"**Status:** {diag['status']} "
                f"(threshold = 0.5)")

    if diag["attackers"]:
        st.markdown("**Threats against your claim:**")
        for a in diag["attackers"]:
            damaging = a["score"] >= 0.5
            icon = "🔴" if damaging else "🟢"
            st.markdown(
                f"- {icon} **{a['id']}** ({a['value_tag']}, w={a['weight']}, "
                f"s={a['score']:.2f}) – {a['text']}"
            )
    else:
        st.success("No active threats. Your claim is unattacked.")

    if diag["supporters"]:
        st.markdown("**Reinforcements for your claim:**")
        for s in diag["supporters"]:
            st.markdown(
                f"- 🟢 **{s['id']}** ({s['value_tag']}, w={s['weight']}, "
                f"s={s['score']:.2f}) – {s['text']}"
            )
    else:
        st.caption("No supports yet. Consider adding one.")


# ============================================================ What-If Sandbox

def _build_hypothetical_engine(messages, mutations):
    """
    Reconstruct an engine from `messages`, applying per-node mutations.

    `mutations` is a dict keyed by message id, with optional fields:
        {"weight": int, "value_tag": str, "deleted": bool}

    Deleted nodes are dropped entirely (along with any edges that
    touched them). Surviving nodes inherit any weight/value_tag
    overrides specified in `mutations`.
    """
    engine = AcademicLogicEngine()
    kept = set()
    for m in messages:
        mid = m["id"]
        mut = mutations.get(mid, {})
        if mut.get("deleted"):
            continue
        weight = mut.get("weight", m.get("weight", 5))
        value_tag = mut.get("value_tag", m.get("value_tag", "Logic"))
        engine.add_argument(mid, m["content"], int(weight), value_tag)
        kept.add(mid)

    for m in messages:
        mid = m["id"]
        if mid not in kept:
            continue
        tgt = m.get("target")
        if not tgt or tgt == "None" or tgt not in kept:
            continue
        if m.get("action") == "Attack":
            engine.add_direct_attack(mid, tgt)
        else:
            engine.add_support(mid, tgt)

    engine.evaluate_semantics()
    return engine


def _render_whatif(engine, messages) -> None:
    if not engine.nodes:
        st.info("No arguments in the graph yet. Make a move first.")
        return

    st.caption(
        "Pick a node and mutate it. The engine recomputes everything in real "
        "time and shows the new verdict on your main claim alongside the "
        "actual verdict."
    )

    if "whatif_mutations" not in st.session_state:
        st.session_state.whatif_mutations = {}
    mutations = st.session_state.whatif_mutations

    node_ids = list(engine.nodes.keys())
    selected = st.selectbox(
        "Choose a node to modify",
        node_ids,
        format_func=lambda mid: (
            f"{mid} [{engine.nodes[mid].get('value_tag', 'Logic')}, "
            f"w={engine.nodes[mid]['weight']}, "
            f"s={engine.scores.get(mid, 1.0):.2f}] "
            f"— {engine.nodes[mid]['text'][:40]}"
        ),
        key="whatif_select",
    )

    current = engine.nodes[selected]
    current_mut = mutations.get(selected, {})

    c1, c2, c3 = st.columns(3)
    with c1:
        new_weight = st.slider(
            "Hypothetical weight",
            min_value=1, max_value=25,
            value=int(current_mut.get("weight", current["weight"])),
            key=f"whatif_weight_{selected}",
            help="Slide to test what would happen at a different weight.",
        )
    with c2:
        valid_tags = list(VALID_VALUE_TAGS)
        new_tag = st.selectbox(
            "Hypothetical value tag",
            valid_tags,
            index=valid_tags.index(
                current_mut.get("value_tag", current.get("value_tag", "Logic"))
            ),
            key=f"whatif_tag_{selected}",
        )
    with c3:
        delete_it = st.checkbox(
            "Delete this node",
            value=bool(current_mut.get("deleted", False)),
            key=f"whatif_del_{selected}",
            help="Remove this argument and any edges that touch it.",
        )

    c_apply, c_reset = st.columns([1, 1])
    with c_apply:
        if st.button("Apply mutation", use_container_width=True,
                     type="primary", key="whatif_apply"):
            mutations[selected] = {
                "weight":    new_weight,
                "value_tag": new_tag,
                "deleted":   delete_it,
            }
            st.session_state.whatif_mutations = mutations
            st.rerun()
    with c_reset:
        if st.button("Reset all mutations", use_container_width=True,
                     key="whatif_reset"):
            st.session_state.whatif_mutations = {}
            st.rerun()

    if not mutations:
        st.info("No mutations applied yet. Set values above and click "
                "**Apply mutation** to see the hypothetical verdict.")
        return

    st.markdown("**Active mutations:**")
    for mid, mut in mutations.items():
        parts = []
        if "weight" in mut and mut["weight"] != engine.nodes.get(mid, {}).get("weight"):
            parts.append(f"weight → {mut['weight']}")
        if "value_tag" in mut and mut["value_tag"] != engine.nodes.get(mid, {}).get("value_tag"):
            parts.append(f"value → {mut['value_tag']}")
        if mut.get("deleted"):
            parts.append("**DELETED**")
        if parts:
            st.markdown(f"  • `{mid}`: " + ", ".join(parts))

    hyp = _build_hypothetical_engine(messages, mutations)

    main_id = "Msg_1"
    real_score = engine.scores.get(main_id, 0.0)
    real_status = engine.statuses.get(main_id, "OUT")
    hyp_score = hyp.scores.get(main_id, 0.0)
    hyp_status = hyp.statuses.get(main_id, "DELETED") if main_id in hyp.nodes else "DELETED"

    st.markdown("---")
    st.markdown("### Verdict on your main claim")
    side_real, side_hyp = st.columns(2)
    with side_real:
        st.metric("Actual", f"{real_score:.3f}  ({real_status})")
    with side_hyp:
        delta = hyp_score - real_score
        st.metric(
            "Hypothetical",
            f"{hyp_score:.3f}  ({hyp_status})",
            delta=f"{delta:+.3f}",
        )

    with st.expander("Show full side-by-side score table", expanded=False):
        rows = []
        all_ids = sorted(set(engine.nodes) | set(hyp.nodes))
        for mid in all_ids:
            real = engine.scores.get(mid)
            hyp_s = hyp.scores.get(mid)
            real_str = f"{real:.3f}" if real is not None else "—"
            hyp_str  = f"{hyp_s:.3f}" if hyp_s is not None else "DELETED"
            rows.append({
                "Node":         mid,
                "Real score":   real_str,
                "Hyp. score":   hyp_str,
                "Real status":  engine.statuses.get(mid, "—"),
                "Hyp. status":  hyp.statuses.get(mid,
                    "DELETED" if mid in mutations and mutations[mid].get("deleted") else "—"),
            })
        st.dataframe(rows, hide_index=True, use_container_width=True)
