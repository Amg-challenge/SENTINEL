"""Test dei contratti tra moduli: se uno di questi fallisce, una firma è cambiata.

Eseguire con:  python -m pytest -q   (oppure: python tests/test_contratti.py)
"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentinel.profiles import PROFILI, COLONNE, genera_storico, inietta_frode, genera_portafoglio
from sentinel.model import adatta_baseline, punteggia
from sentinel.workflow import instrada, richiesta_revoca
from sentinel.economics import (curva_costo, soglia_ottimale, perdita_attesa_evitata, stima_alert,
                                punteggia_portafoglio, riepilogo_portafoglio, applica_soglia_contanti)


def _dati(profilo):
    storico = genera_storico(profilo, giorni=365, seed=1)
    base = adatta_baseline(storico)
    return punteggia(inietta_frode(storico, profilo, n=1, seed=2), base)


def test_dati_hanno_le_colonne_del_contratto():
    for p in PROFILI:
        df = inietta_frode(genera_storico(p, giorni=60), p)
        assert list(df.columns) == COLONNE
        assert df["frode"].sum() > 0


def test_punteggia_aggiunge_colonne_e_ferma_le_frodi():
    for p in PROFILI:
        df = _dati(p)
        assert {"punteggio", "motivi"} <= set(df.columns)
        s = soglia_ottimale(curva_costo(df))
        assert df.loc[df["frode"], "punteggio"].max() >= s, p


def test_conflitto_di_interesse_va_alla_banca():
    figlia = {"nome": "Figlia", "ha_procura": False, "cointestatario": False}
    assert instrada({"avviato_da": "titolare", "beneficiario": ""}, figlia)[0] == "contatto"
    assert instrada({"avviato_da": "titolare", "beneficiario": ""}, {**figlia, "ha_procura": True})[0] == "banca"
    assert instrada({"avviato_da": "titolare", "beneficiario": "Figlia"}, figlia)[0] == "banca"
    assert instrada({"avviato_da": "titolare", "beneficiario": ""}, {**figlia, "raggiungibile": False})[0] == "banca"


def test_revoca_dopo_72_ore():
    r = richiesta_revoca()
    assert (r["effettiva_dal"] - r["richiesta"]).total_seconds() == 72 * 3600


def test_stima_alert_restituisce_le_chiavi_del_pitch():
    df = _dati("truffa_esterna")
    out = stima_alert(df, soglia=soglia_ottimale(curva_costo(df)))
    assert set(out) == {"alert_per_cliente_anno", "quota_contatto", "quota_banca",
                        "casi_banca_per_cliente_anno", "cost_to_serve"}
    assert 0 <= out["quota_banca"] <= 1
    assert perdita_attesa_evitata(df, 0) > 0


def test_portafoglio_colonne_e_periodi():
    port = genera_portafoglio(n_clienti=12, prob_frode=0.5, seed=3)
    assert set(COLONNE) | {"cliente", "profilo", "periodo", "contatto_procura"} == set(port.columns)
    assert port["cliente"].nunique() == 12
    assert set(port["periodo"]) == {"storico", "valutazione"}
    # le frodi cadono sempre nell'anno di valutazione
    assert (port.loc[port["frode"], "periodo"] == "valutazione").all()


def test_stima_alert_e_per_cliente():
    sc = punteggia_portafoglio(genera_portafoglio(n_clienti=12, prob_frode=0.0, seed=3))
    doppio = pd.concat([sc, sc.assign(cliente=sc["cliente"] + 100)], ignore_index=True)
    # raddoppiare i clienti non deve cambiare gli alert PER CLIENTE
    assert stima_alert(sc, 6)["alert_per_cliente_anno"] == stima_alert(doppio, 6)["alert_per_cliente_anno"]
    r = riepilogo_portafoglio(sc, soglia=6)
    assert r["clienti"] == 12 and 0 <= r["quota_banca"] <= 1


def test_soglia_contanti_riduce_gli_alert():
    sc = punteggia_portafoglio(genera_portafoglio(n_clienti=12, prob_frode=0.0, seed=3))
    meno = applica_soglia_contanti(sc, 5_000)
    assert (meno["punteggio"] >= 6).sum() <= (sc["punteggio"] >= 6).sum()


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f(); print("ok ", nome)
