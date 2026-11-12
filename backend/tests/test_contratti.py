"""Contract tests between modules. If one fails, a shared signature or a v6 rule changed.

Run:  python -m pytest -q      (or: python tests/test_contratti.py)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sentinel import economics, model, profiles  # noqa: E402
from sentinel.workflow import (ATTESA_REVOCA_ORE, Contatto, decidi, destinazione_finale,  # noqa: E402
                               instrada, richiesta_revoca)

BASE = model.adatta_baseline(profiles.genera_storico("anziano", seed=7))


def _portafoglio(n=20, prob_frode=0.3, seed=3):
    return economics.punteggia_portafoglio(
        profiles.genera_portafoglio(n_clienti=n, prob_frode=prob_frode, prob_procuratore=0.4, seed=seed))


# ---------------------------------------------------------------- profiles
def test_history_has_contract_columns_and_no_fraud():
    for key in profiles.PRESET:
        df = profiles.genera_storico(key, seed=1, ha_procuratore=True)
        assert list(df.columns) == profiles.COLONNE
        assert set(df["canale"]) <= set(profiles.CANALI)
        assert not df["frode_reale"].any()


def test_every_threat_injects_fraud():
    st = profiles.genera_storico("anziano", seed=1)
    for m in profiles.MINACCE:
        df = profiles.inietta_frode(st, m, seed=2)
        assert df["frode_reale"].sum() >= 1 and list(df.columns) == profiles.COLONNE


def test_portfolio_structure():
    port = profiles.genera_portafoglio(n_clienti=15, prob_frode=0.5, seed=3)
    assert port["cliente"].nunique() == 15
    assert set(port["periodo"]) == {"storico", "valutazione"}
    assert (port.loc[port["frode_reale"], "periodo"] == "valutazione").all()
    assert {"popolazione", "minaccia", "ha_procuratore", "contatto_procura"} <= set(port.columns)


# ---------------------------------------------------------------- model
def test_scores_are_probabilities_and_explainable():
    s = model.punteggia(profiles.genera_storico("anziano", seed=2), BASE)
    assert ((s >= 0) & (s <= 1)).all()
    reasons = model.spiega(dict(canale="sportello", importo=40_000), BASE)
    assert reasons and isinstance(reasons[0][0], str)


def test_amount_keeps_resolution():
    """CHF 40'000 must score clearly above CHF 3'600 (the saturation problem)."""
    hi = model.punteggio(dict(canale="sportello", importo=40_000), BASE)
    lo = model.punteggio(dict(canale="sportello", importo=3_600), BASE)
    assert hi - lo > 0.2


def test_card_payments_out_of_scope():
    assert model.punteggio(dict(canale="carta", importo=5_000, beneficiario="New shop",
                                nuovo_beneficiario=True), BASE) == 0.0


# ---------------------------------------------------------------- workflow (v6 rules)
def test_conflict_of_interest_goes_to_bank():
    anna = Contatto("Anna")
    assert instrada({"avviata_da": "titolare"}, anna)[0] == "contatto"
    assert instrada({"avviata_da": "Anna"}, anna)[0] == "banca"
    assert instrada({"beneficiario": "Anna"}, anna)[0] == "banca"
    assert instrada({}, Contatto("Anna", ha_procura=True))[0] == "banca"
    assert instrada({}, Contatto("Anna", cotitolare=True))[0] == "banca"


def test_no_answer_goes_to_bank_and_bank_alert_pauses():
    op = {"avviata_da": "titolare"}
    assert destinazione_finale(op, Contatto("Anna"), risponde=False, minuti_trascorsi=31)[0] == "banca"
    assert destinazione_finale(op, Contatto("Anna"), risponde=True, minuti_trascorsi=31)[0] == "contatto"
    assert decidi(op, 0.05, 0.5, Contatto("Anna"), alert_esterno=True).in_pausa


def test_revocation_waits_72_hours():
    r = richiesta_revoca()
    assert (r["effettiva_dal"] - r["richiesta"]).total_seconds() == ATTESA_REVOCA_ORE * 3600
    assert r["avviso_contatto"]


# ---------------------------------------------------------------- economics
def test_threshold_and_curves():
    sc = _portafoglio()
    curva, s = economics.calibra_soglia(sc)
    assert 0 <= s <= 1 and {"soglia", "costo"} <= set(curva.columns)
    _, auc = economics.curva_roc(sc.loc[~sc["frode_reale"], "punteggio"], sc.loc[sc["frode_reale"], "punteggio"])
    assert 0.5 < auc <= 1


def test_stima_alert_is_per_customer():
    sc = _portafoglio(prob_frode=0.0)
    doppio = pd.concat([sc, sc.assign(cliente=sc["cliente"] + 1000)], ignore_index=True)
    a, b = economics.stima_alert(sc, 0.5), economics.stima_alert(doppio, 0.5)
    assert a["alert_per_cliente_anno"] == b["alert_per_cliente_anno"]
    assert set(a) >= {"alert_per_cliente_anno", "quota_contatto", "quota_banca", "cost_to_serve"}
    assert 0 <= a["quota_banca"] <= 1


def test_unit_economics_reproduce_v6():
    base = economics.unit_economics_banca("base", 7.0)
    assert base["contribution_annua"] == 73_600 and base["ltv_su_cac"] == 7.4
    assert economics.unit_economics_banca("prudente", 8.0)["contribution_annua"] == 19_200
    assert economics.unit_economics_banca("ottimistico", 7.0)["contribution_annua"] == 138_000


def test_protected_amount_in_range():
    p = economics.importo_protetto(_portafoglio(prob_frode=0.6), 0.5)
    assert 0 <= p["importo_protetto"] <= 1 and 0 <= p["episodi_intercettati"] <= 1


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok ", nome)
