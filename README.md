> **Tim’s fork only:** mock electronic buddy lives in `product/buddy/`.  
> Run: `uv sync` then `uv run streamlit run product/buddy/app.py`  
> See `SANDBOX.md` — do not push this playground to the upstream repo.

### 1. Clone de repo
In VS Code: `Ctrl+Shift+P` → "Git: Clone" → plak de repo-URL → kies een map.
VS Code opent daarna het project.

### 2. Installeer de omgeving
Open een terminal in VS Code (`Ctrl+~`) en run:

    uv sync

Dit leest `uv.lock` en installeert exact dezelfde packages/versies als de rest
van het team. Iedereen heeft nu een identieke omgeving — geen "werkt bij mij
wel"-gedoe.

> Heb je `uv` nog niet? Installeren:
> - **Windows** (PowerShell):
>   `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
> - **Mac/Linux**:
>   `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Selecteer de juiste kernel
Open je notebook (`.ipynb`), klik rechtsboven op "Select Kernel" en kies de
omgeving uit `.venv`. Nu draaien je notebooks in de gedeelde omgeving.

## Dagelijkse workflow

Hou telkens dit ritme aan — dan botst er niets:

1. **PULL**   → haal het nieuwste op vóór je begint
2. **WERK**   → in je EIGEN notebook
3. **COMMIT** → sla je werk op met een kort berichtje
4. **PUSH**   → deel het met de rest

In VS Code doe je dit via de **Source Control-tab** (het vertakkings-icoon links):
Pull via het "..."-menu → Pull; Commit door een bericht te typen + Commit;
Push via Sync / Push.

## Twee gouden regels om conflicten te vermijden

1. **Ieder werkt in zijn eigen notebook.** Nooit met twee mensen tegelijk in
   hetzelfde `.ipynb`.
2. **Losse `.py` files worden bij voorkeur door één persoon tegelijk bewerkt.**

## Package toevoegen tijdens het project

Heb je later nog een package nodig?

    uv add <packagenaam>      # bv. uv add seaborn

Commit + push daarna `pyproject.toml` en `uv.lock`. De rest doet `uv sync` om
bij te blijven.