"""El informe de gobierno debe coincidir con las métricas publicadas y con la regla de dictamen del proyecto."""
import json
from pathlib import Path

import numpy as np

from pqm import viability as vb
from pqm.data import load_secom

ROOT = Path(__file__).resolve().parents[1]


def _historico():
    d = json.loads((ROOT / "reports/metrics.json").read_text(encoding="utf-8"))
    h = d["holdout"]
    _, _, t = load_secom()
    meses = max((t.iloc[-1] - t.iloc[0]).days / 30.44, 1 / 30)
    s, (lo, hi), n, prev = h["ahorro_vs_mejor_baseline"], h["ahorro_ic95"], d["n_holdout"], d["prevalencia_holdout"]
    lotes = int(np.ceil(n * ((s - lo) / s) ** 2))  # misma fórmula que pqm.viability.evaluate
    r = dict(ahorro_ic=(lo, hi), pr_auc_ic=tuple(h["pr_auc_ic95"]), prevalencia_eval=prev, ahorro=s,
             meses_necesarios=max(0.0, (lotes - n) / (len(t) / meses)), fallas_necesarias=int(np.ceil(lotes * prev)),
             ajustes=vb.Ajustes())
    return d, h, r


def test_dictamen_del_caso_historico_segun_la_regla_del_proyecto():
    _, h, r = _historico()
    assert vb.verdict(r)[0] == vb.RECOLECTAR
    assert h["ahorro_ic95"][0] < 0 < h["ahorro_ic95"][1]          # el intervalo incluye pérdidas y ganancias
    assert h["pr_auc_ic95"][0] < r["prevalencia_eval"]            # la señal no está demostrada


def test_cifras_del_informe_coinciden_con_las_metricas():
    d, h, r = _historico()
    texto = (ROOT / "GOVERNANCE_REPORT.md").read_text(encoding="utf-8")
    esperadas = [f"{h['ahorro_ic95'][0]:,.0f}", f"+{h['ahorro_ic95'][1]:,.0f}", f"{h['costo_con_modelo']:,.0f}",
                 f"{h['costo_sin_modelo']:,.0f}", f"{h['costo_inspeccionar_todo']:,.0f}", f"{h['ahorro_vs_mejor_baseline']:,.0f}",
                 f"{h['pr_auc']:.3f}", f"{h['pr_auc_ic95'][0]:.3f} – {h['pr_auc_ic95'][1]:.3f}",
                 f"{d['prevalencia_holdout']:.3f}", f"{h['detectadas']} de {d['fallas_holdout']}", f"{h['falsas_alarmas']} falsas",
                 f"≈ {r['fallas_necesarias']} fallas", "RECOLECTAR MÁS DATOS"]
    for s in d["sensibilidad_costos"]:
        esperadas.append(f"{'+' if s['ahorro'] > 0 else '−'}{abs(s['ahorro']):,.0f} (×{s['razon_scrap_inspeccion']}")
    faltan = [e for e in esperadas if e.replace("−", "-") not in texto.replace("−", "-")]
    assert not faltan, faltan


def test_readme_no_promete_ahorro_demostrado():
    for nombre in ("README.md", "README.es.md"):
        texto = (ROOT / nombre).read_text(encoding="utf-8")
        assert "GOVERNANCE_REPORT.md" in texto
