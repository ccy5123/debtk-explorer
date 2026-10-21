# DEB-TK fish bioconcentration explorer

A Streamlit app that computes how much of a chemical a growing fish takes up from water and how long it keeps
it, with the DEB-TK framework (Lee & Joe, ChemRxiv `10.26434/chemrxiv.15002330/v1`). Water exposure only; the
dietary pathway is not implemented.

```bash
pip install -r requirements.txt
streamlit run app.py
```

| | |
|---|---|
| `app.py` | the interface |
| `debtk/model.py` | the equations: gill uptake, respiratory elimination, biotransformation, growth dilution, BCF, and the time integration |
| `debtk/data.py` | reads the two data files below |
| `debtk/ctx.py` | EPA CompTox lookup for chemicals outside the library |
| `debtk/fish_svg.py`, `assets/fish.svg` | the fish drawing |
| `debtk/panels.py`, `debtk/i18n.py` | charts; English and Korean text |
| `data/sim_data.json` | 866 structures with their partition coefficients at 15, 22 and 25 °C, and the gill settings |
| `data/fish_species.json` | 3,039 Add-my-Pet fish entries |

CompTox lookups need a key, read from `ctx_api_key` in Streamlit secrets, from `EPA_API_KEY` or `CTX_API_KEY`
in the environment, or typed into the sidebar. The key is never stored in this repository.
