"""Actionable intervention detail pages (Dutch, coaching, no medical claims)."""

from __future__ import annotations

from typing import Any

# Theme keys match intervention "theme" in the persona fixtures.

MOVEMENT_GRONINGEN: dict[str, Any] = {
    "theme": "sport",
    "kicker": "Beweging · Groningen",
    "title": "Een vriendelijke lus: Noorderplantsoen → grachten → Martinitoren",
    "coach": (
        "Geen schema voor atleten — een rondje dat je kunt onthouden. "
        "Groen, water, en de toren als herkenningspunt. Trek je jas aan en begin klein."
    ),
    "why": (
        "Regelmatig wandelen is een leefstijlknop die vaak samenhangt met gewicht, taille "
        "en hoe je lichaam suiker verwerkt. Deze demo koppelt dat aan een lager "
        "korte- en lange-termijn risico-beeld (proxy: HbA1c). Het is coaching, "
        "geen diagnose en geen trainingsvoorschrift."
    ),
    "when": "Het liefst na een maaltijd, drie keer deze week — dezelfde schoenen, hetzelfde startpunt.",
    "duration": "30–45 minuten (ongeveer 3,5 km). Liever 25 minuten volhouden dan 60 minuten uitstellen.",
    "intensity": "Stevig wandeltempo: je kunt nog praten, je hoeft niet te hijgen. Bankjes onderweg zijn oké.",
    "route_name": "Plantsoen–gracht–Martini-lus",
    "route_steps": [
        "Start bij de hoofdingang van het Noorderplantsoen (Kruissingel / Oranjesingel).",
        "Loop het park rond: blijf bij de vijver en de grote bomen, met de klok mee.",
        "Verlaat het plantsoen richting de Noorderhaven en volg het water de stad in.",
        "Houd de Diepenring aan tot je de Martinitoren goed ziet (Vismarkt / Grote Markt-kant).",
        "Keer terug via de Nieuwe Ebbingestraat of Boteringestraat naar het plantsoen — lus sluiten.",
    ],
    "tip": "Regendag? Doe alleen het plantsoenrondje (15–20 min) en streep de week niet weg.",
}

FOOD_STUB: dict[str, Any] = {
    "theme": "food",
    "kicker": "Voeding · voorstel (stub)",
    "title": "Eén suikerdrank minder, dezelfde koffieafspraak",
    "coach": (
        "Niet een heel dieet omgooien. Kies één vast moment — bijvoorbeeld de middag op het Forum "
        "of thuis na het eten — en wissel het suikerdrankje in voor water of thee zonder suiker."
    ),
    "why": (
        "Rustige maaltijden en minder suikerhoudende dranken zijn leefstijlkeuzes die in deze demo "
        "gekoppeld zijn aan BMI en taille. Dat kan het risico-beeld iets rustiger maken. "
        "Geen dieetvoorschrift, geen medisch advies."
    ),
    "when": "Kies één vast moment per dag, zeven dagen achter elkaar.",
    "duration": "De wissel zelf duurt geen extra tijd — alleen de keuze.",
    "intensity": "Klein en saai is beter dan streng en kort.",
    "route_name": "Eerste stap",
    "route_steps": [
        "Schrijf op welk drankje je meestal neemt (frisdrank, sap, zoete koffie).",
        "Zet het alternatief al klaar: fles water of thee.",
        "Vink één dag af. Morgen hetzelfde moment.",
    ],
    "tip": "Uitgebreide weekmenu’s komen later — dit scherm is expres een stub.",
}

SLEEP_STUB: dict[str, Any] = {
    "theme": "sleep",
    "kicker": "Slaap · voorstel (stub)",
    "title": "Telefoon de kamer uit, dezelfde bedtijd",
    "coach": (
        "Slaap is geen prestatie. Een vast avondritueel maakt de dag kleiner, "
        "niet perfecter."
    ),
    "why": (
        "Onregelmatige slaap hoort in deze demo bij het lokale risico-beeld. "
        "Een rustiger avond is leefstijlcoaching, geen behandeling van slaapproblemen."
    ),
    "when": "Dertig minuten voor je gekozen bedtijd, vijf avonden deze week.",
    "duration": "30 minuten schermvrij — niet meer.",
    "intensity": "Licht dimmen, geen extra oefeningen verplicht.",
    "route_name": "Eerste stap",
    "route_steps": [
        "Kies een bedtijd die je twee avonden achter elkaar kunt herhalen.",
        "Leg de telefoon in een andere kamer, niet op het nachtkastje.",
        "Doe één rustig ding: thee, boek, of alleen het licht lager.",
    ],
    "tip": "Stub: later kunnen we dit koppelen aan jouw slaapfactor.",
}

GENERIC_STUB: dict[str, Any] = {
    "theme": "generic",
    "kicker": "Leefstijl · voorstel (stub)",
    "title": "Eén kleine herhaalbare stap",
    "coach": "We werken dit thema later uit. Voor nu: kies één ding dat je morgen opnieuw kunt doen.",
    "why": "Leefstijlknoppen horen bij het demobeeld, niet bij medicatie of triage.",
    "when": "Morgen, op een vast tijdstip.",
    "duration": "Tien minuten is genoeg om te starten.",
    "intensity": "Laag. Herhalen telt meer dan zwaar.",
    "route_name": "Eerste stap",
    "route_steps": [
        "Kies één gewoonte die al een beetje lukt.",
        "Herhaal die morgen op hetzelfde moment.",
    ],
    "tip": "Geen medisch advies — praat met je zorgverlener over klachten of medicijnen.",
}

PAGES = {
    "sport": MOVEMENT_GRONINGEN,
    "food": FOOD_STUB,
    "sleep": SLEEP_STUB,
    "smoking": {
        **GENERIC_STUB,
        "theme": "smoking",
        "kicker": "Rookvrij · voorstel (stub)",
        "title": "Twee rookvrije blokken deze week",
        "coach": "Geen stoppen-met-roken-kuur hier. Wel twee blokken die je zelf kiest — de fietsrit telt mee.",
    },
    "alcohol": {
        **GENERIC_STUB,
        "theme": "alcohol",
        "kicker": "Alcohol · voorstel (stub)",
        "title": "Twee avonden zonder alcohol",
        "coach": "Geen verbod. Twee doordeweekse avonden met bruiswater dat je echt lust.",
    },
}


def get_intervention_page(theme: str) -> dict[str, Any]:
    return PAGES.get(theme) or {**GENERIC_STUB, "theme": theme}
