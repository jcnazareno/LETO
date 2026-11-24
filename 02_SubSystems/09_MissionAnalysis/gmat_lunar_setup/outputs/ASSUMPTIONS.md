# Current GMAT assumptions

**Option A study setup; not an adopted flight design.** User-confirmed architecture, epoch and sensitivity approach for this study; spacecraft properties remain provisional. The 2031 epoch is provisional.

| Input | Current value |
|---|---|
| Epoch / start | **2031-01-01 00:00 UTC**; already captured in lunar orbit |
| Monitoring → imaging | **3000 km / 913.125 d → 300 km / 182.625 d**; year = **365.25 d** |
| Initial orbit | Circular; **90° to instantaneous DE421 lunar pole**; ascending PA longitude **0°**; northward velocity |
| Lunar reference | Spherical **1738 km**; μ **4902.79996708864 km³/s²** |
| Gravity / ephemeris | **GRGM900C 80×80**, fully normalized; matched **DE421 PA / DE421** |
| Solid tides | **k₂₀ = k₂₁ = k₂₂ = 0.024116** |
| Third bodies | Earth, Sun, Jupiter, Venus, Mars, Saturn; point masses |
| Relativity / drag | **On / None** |
| Mass | Dry **118.1 kg**; launch **189.9099 kg**; science start **153.3540 kg** |
| Propulsion | Capture allowance **629 m/s**; **Isp 300 s**, g₀ **9.80665 m/s²** |
| SRP nominal | Effective area **1.2 m²**, **Cr 1.5**; **1361 W/m²** at **149597870.7 km**; conical Moon/Earth shadows |
| SRP brackets | Low **0.7 m² / Cr 1.2**; high **2.0 m² / Cr 1.8**; not probability intervals |
| Lowering | Two targeted ideal impulses; seeds ≈**−228 / −283 m/s**; target radius/SMA **2038 km** |
| Targeter | Tolerance **0.01 km**; ≤**40** iterations; perturbation **0.01 m/s**, step ≤**100 m/s**, bounds **±800 m/s** |
| Ideal maintenance | **e > 0.02**; **1 d** checks on hourly grid; circularize at **current radius** |
| Integrator | Prince–Dormand 7/8; accuracy **10⁻¹¹**; initial/min/max steps **10/0.001/60 s**; ≤**100** attempts |
| Output / guard | **3600 s** samples; stop at **20 km** spherical radius altitude |
| Attitude | Kinematic nadir: **+Z** toward Moon, **+Y** orbit-normal; no ADCS dynamics |
| Separate screens only | Inertias **[15,20,25] kg·m²**; arm **0.02 m**; misalignment **1°**; lunar disk **400 K**, reflectance **0.12**, momentum factor **2** |
| Short tests | **30 d** per altitude; transfer **2 d + coasts + 2 d**; gravity **40/80/120** and SRP comparisons **7 d** |
| Numerical / controller checks | Tight **10⁻¹², 30 s**, **7 d**; artificial controller **e > 10⁻⁷**, **3 d** |

**Critical (documentation checked 11 November 2026):** no completed full-mission propagation is recorded; a partial ideal-maintenance history reaches 7.375 d. Initial plane unoptimized. Maintenance holds neither altitude nor plane. Impulses assume exact navigation/execution. No terrain clearance, future leap-second prediction, finite burns, propagated lunar albedo/IR or thermal recoil, plume/exosphere, magnetic, radiation-damage or jitter model. No coverage, lifetime, pointing or annual Δv claim.

Exact configuration: [`config.json`](../analysis/gmat_lunar_setup/config.json). Derived states, masses and hashes: each script’s `.manifest.json` in [`scripts/`](scripts); histories remain in [`runs/`](runs).
