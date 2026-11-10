"""Synthetic transaction histories: populations, legitimate behaviour, threats.

Owner: Utente 2 · branch `dati-economia`.

No real customer data is used anywhere. We generate the *normal* behaviour of a
person (weekly cash, card spending, monthly bills, a few unusual but legitimate
events) and then inject one of the three threats of the pitch (document v6):

    truffa_esterna   fake police officer / fake grandchild: cash at the counter,
                     sometimes after emptying the safe deposit box
    abuso_interno    someone holding a power of attorney drains the account
                     with repeated ATM withdrawals
    bonifico_estero  pressured transfer to a new foreign account

The unusual-but-legitimate events matter: without them the synthetic customer
is too regular, the engine raises no false alarms and the operational load
(alerts, cost to serve) comes out unrealistically low.

CONTRACT (stable signatures, change only with the group's agreement):
    genera_storico(cfg, giorni=365, seed=0, ha_procuratore=False) -> DataFrame
    inietta_frode(storico, minaccia="truffa_esterna", seed=0, importo=None) -> DataFrame
    genera_frodi_simulate(n=300, seed=1, mix=None) -> DataFrame
    genera_portafoglio(n_clienti=300, ...) -> DataFrame

Columns (COLONNE):
    data (Timestamp), canale ("sportello" | "bancomat" | "cassetta" | "bonifico" | "carta"),
    importo (CHF), beneficiario (str, "" for cash), nuovo_beneficiario (bool),
    estero (bool), avviata_da ("titolare" | "procuratore" | a person's name),
    alert_banca (bool: flagged by the bank's own antifraud, e.g. NetGuardians),
    frode_reale (bool: ground truth, never used by the engine)
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

COLONNE = ["data", "canale", "importo", "beneficiario", "nuovo_beneficiario",
           "estero", "avviata_da", "alert_banca", "frode_reale"]
CANALI = ("sportello", "bancomat", "cassetta", "bonifico", "carta")

MINACCE: dict[str, str] = {
    "truffa_esterna": "External scam: cash at the counter (fake police officer)",
    "abuso_interno": "Internal abuse: power-of-attorney holder drains the account",
    "bonifico_estero": "Pressured transfer to a new foreign account",
}


@dataclass
class ProfiloConfig:
    """Parameters of a population's normal behaviour (amounts in CHF, rates per year)."""

    nome: str
    prelievo_medio: float              # weekly cash withdrawal
    prelievo_sd: float
    quota_sportello: float             # share of weekly withdrawals made at the counter
    spesa_media: float                 # typical card purchase
    beneficiari_noti: list[str] = field(default_factory=list)       # card merchants
    bollette: list[tuple[str, float, float]] = field(default_factory=list)  # monthly transfers
    # unusual but legitimate events (yearly frequency, amount range)
    eventi_straordinari: float = 3.0   # payments to a never-seen payee (dentist, plumber)
    straordinario_min: float = 500.0
    straordinario_max: float = 3000.0
    beneficiari_straordinari: list[str] = field(default_factory=list)
    prelievi_straordinari: float = 2.0  # large cash withdrawals at the counter (holiday, gift)
    prelievo_straord_min: float = 1500.0
    prelievo_straord_max: float = 6000.0
    bonifici_esteri: float = 0.5       # legitimate transfers abroad (family, holidays)
    accessi_cassetta: float = 1.0      # legitimate safe-deposit-box visits
    falsi_alert_banca: float = 0.3     # bank antifraud false positives on normal payments
    spesa_procuratore: tuple[float, float] = (100.0, 250.0)  # monthly, if there is a POA holder


# One engine, three populations. "anziano" is the first target of the pitch;
# "curatela" is the expansion; "prudente" is the long-term vision (anyone who opts in).
PRESET: dict[str, ProfiloConfig] = {
    "anziano": ProfiloConfig(
        "Independent senior (65+)", prelievo_medio=250, prelievo_sd=60, quota_sportello=0.3,
        spesa_media=35, beneficiari_noti=["Coop", "Migros", "Pharmacy", "Post office"],
        bollette=[("Health insurance", 350, 600), ("Rent", 1200, 2000),
                  ("Electricity", 60, 150), ("Telephone", 40, 90)],
        eventi_straordinari=3, straordinario_min=500, straordinario_max=3000,
        beneficiari_straordinari=["Dentist", "Appliances", "Travel agency", "Plumber",
                                  "Gift for grandchild"],
        prelievi_straordinari=2.0, prelievo_straord_min=1500, prelievo_straord_max=6000,
        bonifici_esteri=0.5, accessi_cassetta=1.0, falsi_alert_banca=0.3,
    ),
    "curatela": ProfiloConfig(
        "Person under guardianship", prelievo_medio=180, prelievo_sd=20, quota_sportello=0.2,
        spesa_media=20, beneficiari_noti=["Supermarket", "Pharmacy", "Day centre"],
        bollette=[("Rent", 900, 1300), ("Health insurance", 300, 450), ("Telephone", 30, 60)],
        eventi_straordinari=2, straordinario_min=300, straordinario_max=1200,
        beneficiari_straordinari=["Optician", "Clothing", "Dentist"],
        prelievi_straordinari=0.5, prelievo_straord_min=500, prelievo_straord_max=1500,
        bonifici_esteri=0.1, accessi_cassetta=0.2, falsi_alert_banca=0.2,
    ),
    "prudente": ProfiloConfig(
        "Prudent adult (opt-in)", prelievo_medio=400, prelievo_sd=120, quota_sportello=0.1,
        spesa_media=60, beneficiari_noti=["Amazon", "Restaurant", "SBB", "Petrol", "Coop"],
        bollette=[("Rent", 1800, 2600), ("Health insurance", 350, 500), ("Car leasing", 400, 600)],
        eventi_straordinari=5, straordinario_min=800, straordinario_max=5000,
        beneficiari_straordinari=["Garage", "Dentist", "Travel", "Furniture", "Plumber"],
        prelievi_straordinari=1.0, prelievo_straord_min=1000, prelievo_straord_max=4000,
        bonifici_esteri=1.5, accessi_cassetta=0.5, falsi_alert_banca=0.5,
    ),
}

INIZIO = pd.Timestamp("2025-01-06")  # a Monday


def _riga(data, canale, importo, beneficiario="", nuovo=False, estero=False,
          avviata_da="titolare", alert_banca=False, frode=False) -> dict:
    return dict(data=data, canale=canale, importo=round(float(importo), 2),
                beneficiario=beneficiario, nuovo_beneficiario=bool(nuovo), estero=bool(estero),
                avviata_da=avviata_da, alert_banca=bool(alert_banca), frode_reale=bool(frode))


def _cfg(cfg: ProfiloConfig | str) -> ProfiloConfig:
    return PRESET[cfg] if isinstance(cfg, str) else cfg


def genera_storico(cfg: ProfiloConfig | str, giorni: int = 365, seed: int = 0,
                   ha_procuratore: bool = False) -> pd.DataFrame:
    """Legitimate history of one customer (no fraud). `cfg` is a ProfiloConfig or a PRESET key.

    Each customer has their own spending scale (log-normal, sigma 0.3), so two
    customers of the same population do not look identical.
    """
    cfg = _cfg(cfg)
    rng = np.random.default_rng(seed)
    scala = float(rng.lognormal(0.0, 0.3))
    anni = giorni / 365
    righe: list[dict] = []

    for g in range(giorni):
        giorno = INIZIO + pd.Timedelta(days=g)
        if giorno.weekday() == 0:  # weekly cash
            canale = "sportello" if rng.random() < cfg.quota_sportello else "bancomat"
            imp = max(20.0, rng.normal(cfg.prelievo_medio, cfg.prelievo_sd)) * scala
            righe.append(_riga(giorno, canale, imp))
        for _ in range(int(rng.poisson(3 / 7))):  # card purchases, ~3 per week
            imp = max(5.0, rng.normal(cfg.spesa_media, cfg.spesa_media * 0.4)) * scala
            righe.append(_riga(giorno, "carta", imp,
                               beneficiario=str(rng.choice(cfg.beneficiari_noti))))
        if giorno.day == 1:  # monthly bills to known payees
            for nome, lo, hi in cfg.bollette:
                righe.append(_riga(giorno, "bonifico", rng.uniform(lo, hi) * scala, beneficiario=nome))
        if ha_procuratore and giorno.day == 15:  # legitimate errands by the POA holder
            lo, hi = cfg.spesa_procuratore
            righe.append(_riga(giorno, "bancomat", rng.uniform(lo, hi) * scala, avviata_da="procuratore"))

    def eventi(rate: float) -> list[pd.Timestamp]:
        return [INIZIO + pd.Timedelta(days=int(rng.integers(0, giorni)))
                for _ in range(int(rng.poisson(rate * anni)))]

    for d in eventi(cfg.eventi_straordinari):
        ben = f"{rng.choice(cfg.beneficiari_straordinari or ['Other'])} #{rng.integers(100, 999)}"
        righe.append(_riga(d, "bonifico" if rng.random() < 0.6 else "carta",
                           rng.uniform(cfg.straordinario_min, cfg.straordinario_max) * scala,
                           beneficiario=ben, nuovo=True))
    for d in eventi(cfg.prelievi_straordinari):
        righe.append(_riga(d, "sportello",
                           rng.uniform(cfg.prelievo_straord_min, cfg.prelievo_straord_max) * scala))
    for d in eventi(cfg.bonifici_esteri):
        righe.append(_riga(d, "bonifico", rng.uniform(300, 3000) * scala,
                           beneficiario=f"Relative abroad #{rng.integers(100, 999)}",
                           nuovo=True, estero=True))
    for d in eventi(cfg.accessi_cassetta):
        righe.append(_riga(d, "cassetta", 0.0))
    for d in eventi(cfg.falsi_alert_banca):
        nome, lo, hi = cfg.bollette[0]
        righe.append(_riga(d, "bonifico", rng.uniform(lo, hi) * scala, beneficiario=nome,
                           alert_banca=True))

    df = pd.DataFrame(righe, columns=COLONNE)
    return df.sort_values("data", kind="stable").reset_index(drop=True)


def _operazioni_frode(minaccia: str, giorno: pd.Timestamp, rng: np.random.Generator,
                      importo: float | None = None) -> list[dict]:
    """Fraudulent operations of one episode. Amounts are deliberately varied and overlap
    with legitimate unusual spending (assumptions to calibrate with Utente 1's sources)."""
    ops: list[dict] = []
    if minaccia == "truffa_esterna":
        totale = importo or float(np.clip(rng.lognormal(np.log(10_000), 0.9), 1_000, 80_000))
        if rng.random() < 0.5:  # empties the safe deposit box first
            ops.append(_riga(giorno, "cassetta", 0.0, frode=True))
        if rng.random() < 0.3 and importo is None:  # split over two days
            q = rng.uniform(0.4, 0.6)
            ops.append(_riga(giorno, "sportello", totale * q, frode=True))
            ops.append(_riga(giorno + pd.Timedelta(days=1), "sportello", totale * (1 - q), frode=True))
        else:
            ops.append(_riga(giorno, "sportello", totale, frode=True))
    elif minaccia == "abuso_interno":
        for k in range(int(rng.integers(4, 11))):  # gradual: hard to see
            ops.append(_riga(giorno + pd.Timedelta(days=7 * k), "bancomat",
                             importo or rng.uniform(300, 1_000), avviata_da="procuratore", frode=True))
    elif minaccia == "bonifico_estero":
        imp = importo or float(np.clip(rng.lognormal(np.log(8_000), 0.8), 1_000, 60_000))
        ops.append(_riga(giorno, "bonifico", imp, beneficiario=f"Foreign IBAN #{rng.integers(1000, 9999)}",
                         nuovo=True, estero=True, alert_banca=bool(rng.random() < 0.6), frode=True))
    else:
        raise ValueError(f"Unknown threat: {minaccia}. Available: {list(MINACCE)}")
    return ops


def inietta_frode(storico: pd.DataFrame, minaccia: str = "truffa_esterna", seed: int = 0,
                  importo: float | None = None) -> pd.DataFrame:
    """Append one fraud episode after the end of the history. `importo` forces the amount (demo)."""
    rng = np.random.default_rng(seed)
    giorno = storico["data"].max() + pd.Timedelta(days=2)
    nuove = pd.DataFrame(_operazioni_frode(minaccia, giorno, rng, importo), columns=COLONNE)
    return pd.concat([storico, nuove], ignore_index=True)


def genera_frodi_simulate(n: int = 300, seed: int = 1, mix: dict | None = None) -> pd.DataFrame:
    """A sample of fraudulent operations (no dates needed) for ROC and cost curves."""
    mix = mix or {"truffa_esterna": 0.5, "bonifico_estero": 0.3, "abuso_interno": 0.2}
    rng = np.random.default_rng(seed)
    nomi, p = list(mix), np.array(list(mix.values()), dtype=float)
    righe: list[dict] = []
    while len(righe) < n:
        righe += _operazioni_frode(str(rng.choice(nomi, p=p / p.sum())), pd.NaT, rng)
    df = pd.DataFrame(righe[:n], columns=COLONNE)
    df["data"] = pd.NaT
    return df


def genera_portafoglio(n_clienti: int = 300, mix_popolazione: dict | None = None,
                       prob_frode: float = 0.01, prob_procuratore: float = 0.15,
                       prob_contatto_con_procura: float = 0.5, eventi: dict | None = None,
                       seed: int = 0) -> pd.DataFrame:
    """A simulated book of customers, to measure alerts and cost to serve on real numbers.

    Each customer gets two years: the first ("storico") teaches the engine their habits,
    the second ("valutazione") is where alerts are counted. With probability `prob_frode`
    the customer suffers one fraud episode in the second year.

    - `prob_procuratore`: share of customers with someone holding a power of attorney.
    - `prob_contatto_con_procura`: if there is one, probability that this person is
      also the trusted contact (then every alert goes to the bank: conflict of interest).
    - `eventi`: overrides of ProfiloConfig fields for every population (sensitivity).

    1% of customers defrauded per year is an assumption to calibrate (Utente 1). To
    measure the detection rate, oversample (e.g. 0.10): it does not change the alerts
    on legitimate customers.

    Extra columns: cliente, popolazione, minaccia ("" if none), periodo
    ("storico" | "valutazione"), ha_procuratore, contatto_procura.
    """
    mix = mix_popolazione or {"anziano": 1.0}
    rng = np.random.default_rng(seed)
    pop, pesi = list(mix), np.array(list(mix.values()), dtype=float)
    pesi = pesi / pesi.sum()
    confine = INIZIO + pd.Timedelta(days=365)
    pezzi = []
    for c in range(n_clienti):
        chiave = str(rng.choice(pop, p=pesi))
        cfg = replace(PRESET[chiave], **(eventi or {}))
        procuratore = bool(rng.random() < prob_procuratore)
        df = genera_storico(cfg, giorni=730, seed=seed * 100_000 + c, ha_procuratore=procuratore)
        minaccia = ""
        if rng.random() < prob_frode:
            opzioni = (["truffa_esterna", "bonifico_estero", "abuso_interno"], [0.4, 0.3, 0.3]) \
                if procuratore else (["truffa_esterna", "bonifico_estero"], [0.6, 0.4])
            minaccia = str(rng.choice(opzioni[0], p=opzioni[1]))
            giorno = INIZIO + pd.Timedelta(days=int(rng.integers(380, 700)))
            df = pd.concat([df, pd.DataFrame(_operazioni_frode(minaccia, giorno, rng), columns=COLONNE)],
                           ignore_index=True).sort_values("data", kind="stable").reset_index(drop=True)
        pezzi.append(df.assign(
            cliente=c, popolazione=chiave, minaccia=minaccia,
            periodo=np.where(df["data"] < confine, "storico", "valutazione"),
            ha_procuratore=procuratore,
            contatto_procura=bool(procuratore and rng.random() < prob_contatto_con_procura)))
    return pd.concat(pezzi, ignore_index=True)
