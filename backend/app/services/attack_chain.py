"""Build attack-chain graph nodes/edges from MITRE techniques, IOCs, and sector context."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.schemas import AttackChainEdge, AttackChainGraph, AttackChainNode, Industry, IOC, MitreTechnique
from app.services.mitre_tactic_map import TACTIC_ORDER, tactic_for_technique

if TYPE_CHECKING:
    pass


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")


def _sector_risk_label(industry: Industry) -> str | None:
    return {
        "healthcare": "PHI exposure — HIPAA risk",
        "finance": "Fraud / wire-transfer exposure",
        "manufacturing": "OT boundary / engineering access risk",
        "energy": "ICS process manipulation risk",
        "government": "Sensitive identity / credential risk",
        "cloud": "IAM blast-radius / cloud takeover risk",
        "default": None,
    }.get(industry)


def build_attack_chain_graph(
    log_text: str,
    industry: Industry,
    severity: str,
    techniques: list[MitreTechnique],
    iocs: list[IOC],
) -> AttackChainGraph:
    log_lower = log_text.lower()
    nodes: list[AttackChainNode] = []
    edges: list[AttackChainEdge] = []
    edge_i = 0

    # Layer X positions: tactics row, techniques row, IOCs row
    tactic_x: dict[str, float] = {}
    x_step = 220.0
    x0 = 40.0
    for tac in TACTIC_ORDER:
        tactic_x[tac] = x0
        x0 += x_step * 0.35
    # Pack only used tactics to the left
    used_tactics: dict[str, int] = {}
    for mt in techniques:
        tac = tactic_for_technique(mt.id)
        used_tactics[tac] = used_tactics.get(tac, 0) + 1

    tx = 80.0
    for tac in TACTIC_ORDER:
        if tac not in used_tactics:
            continue
        tid = f"tactic-{_slug(tac)}"
        nodes.append(
            AttackChainNode(
                id=tid,
                node_type="tactic",
                label=tac,
                mitre_id=None,
                mitre_url=None,
                confidence=None,
                ioc_type=None,
                position={"x": tx, "y": 40.0},
            )
        )
        tx += 200.0

    # Sector risk node (purple)
    sr = _sector_risk_label(industry)
    if sr:
        nodes.append(
            AttackChainNode(
                id="sector-risk",
                node_type="sector_risk",
                label=sr,
                mitre_id=None,
                mitre_url=None,
                confidence=None,
                ioc_type=None,
                position={"x": 320.0, "y": 0.0},
            )
        )

    # Techniques (orange)
    ty = 160.0
    for idx, mt in enumerate(techniques[:10]):
        tac = tactic_for_technique(mt.id)
        parent = f"tactic-{_slug(tac)}"
        nid = f"tech-{_slug(mt.id)}"
        nodes.append(
            AttackChainNode(
                id=nid,
                node_type="technique",
                label=f"{mt.id} — {mt.name[:40]}",
                mitre_id=mt.id,
                mitre_url=mt.url,
                confidence=mt.confidence,
                ioc_type=None,
                position={"x": 60.0 + idx * 190.0, "y": ty},
            )
        )
        if any(n.id == parent for n in nodes):
            edges.append(
                AttackChainEdge(
                    id=f"e{edge_i}",
                    source=parent,
                    target=nid,
                    label="technique",
                    strength=mt.confidence,
                )
            )
            edge_i += 1
        elif sr:
            edges.append(
                AttackChainEdge(
                    id=f"e{edge_i}",
                    source="sector-risk",
                    target=nid,
                    label="sector context",
                    strength=0.4,
                )
            )
            edge_i += 1

    # IOCs (red)
    iy = 300.0
    for j, ioc in enumerate(iocs[:12]):
        nid = f"ioc-{_slug(ioc.type)}-{j}"
        in_log = ioc.value.lower() in log_lower if ioc.value else False
        strength = 0.85 if in_log else 0.45
        nodes.append(
            AttackChainNode(
                id=nid,
                node_type="ioc",
                label=f"{ioc.type}: {ioc.value[:48]}{'…' if len(ioc.value) > 48 else ''}",
                mitre_id=None,
                mitre_url=None,
                confidence=strength,
                ioc_type=ioc.type,
                position={"x": 50.0 + j * 175.0, "y": iy},
            )
        )
        # Link to best-matching technique (by substring) or first technique
        best_tech = None
        for mt in techniques:
            if mt.id.lower() in log_lower or (mt.name and mt.name.lower()[:20] in log_lower):
                best_tech = mt
                break
        if best_tech is None and techniques:
            best_tech = techniques[0]
        if best_tech:
            tid = f"tech-{_slug(best_tech.id)}"
            if any(n.id == tid for n in nodes):
                edges.append(
                    AttackChainEdge(
                        id=f"e{edge_i}",
                        source=tid,
                        target=nid,
                        label=f"observed {ioc.type}",
                        strength=strength,
                    )
                )
                edge_i += 1

    # Connect sector to first tactic if present
    if sr and nodes:
        first_tac = next((n for n in nodes if n.node_type == "tactic"), None)
        if first_tac and not any(e.source == "sector-risk" and e.target == first_tac.id for e in edges):
            edges.append(
                AttackChainEdge(
                    id=f"e{edge_i}",
                    source="sector-risk",
                    target=first_tac.id,
                    label="risk context",
                    strength=0.35,
                )
            )

    return AttackChainGraph(nodes=nodes, edges=edges)
