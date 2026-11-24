# Supporting-studies explorer

The [explorer](../../outputs/studies_explorer.html) uses the recorded results from the radiation, orbit and attitude, LUMIO comparison, and D01–D04 flash photon-budget studies. The original study conditions are retained.

Run from the project root to rebuild the data and page:

```bash
python3 analysis/studies_explorer/studies_data.py
python3 analysis/studies_explorer/build_studies_explorer.py
```

The build uses the Python standard library. The charts use Chart.js 4.4.1. The crater test has its own [methods and results](../crater_injection_test/README.md).
