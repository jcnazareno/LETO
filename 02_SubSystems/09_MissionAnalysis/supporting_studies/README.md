# Lunar mission supporting studies

- [Supporting-studies explorer](outputs/studies_explorer.html) and [rebuild commands](analysis/studies_explorer/README.md)
- [Radiation environment](outputs/radiation_environment_research_2026-10-29/README.md)
- [Event-sensor trade](outputs/sensor_trade/sensor_trade.md)
- [Orbit and attitude disturbances](outputs/disturbance_environment_research_2026-10-29/README.md)
- [LUMIO comparison](outputs/lumio_comparison_research_2026-10-29/README.md)
- [D01–D04 flash photon budget](outputs/d01_d04_research_2026-10-28/d01_d04_research.md)
- [Crater-injection test](analysis/crater_injection_test/README.md), [first results](outputs/crater_test/crater_test_results.md) and [real-crater follow-up](outputs/lroc_lola_update/lroc_lola_update.md)

The explorer rebuilds from local study results. The real-new-crater workflow uses the original NAC CDR images, catalogue, WAC and LOLA data under `data/external/`.

The source SMD folder lacks the four CraterDANet image and label pairs used in the first injection test, the radiation study's original digitization raster, and the disturbance study's original source cache. Recorded outputs are included for these analyses. Source names and provenance are recorded in their methods and data directories.
