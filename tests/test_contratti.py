"""Test dei contratti tra moduli: se uno di questi fallisce, una firma è cambiata.

Eseguire con:  python -m pytest -q   (oppure: python tests/test_contratti.py)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentinel.profiles import PROFILI, COLONNE, genera_storico, inietta_frode
from sentinel.model import adatta_baseline, punteggia
from sentinel.workflow import instrada, richiesta_revoca
from sentinel.economics import curva_costo, soglia_ottimale, perdita_attesa_evitata, stima_alert


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


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f(); print("ok ", nome)
