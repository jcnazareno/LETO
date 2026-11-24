"""Build the concise internal D01-D04 PDF report using the reviewed research snapshot (prose restyled 2 November 2026; content unchanged).

Dependencies: ReportLab, pypdf; bundled Python. Run from the workspace root.
Inputs: model_results.json, lightcurve_results.json and cited figure excerpts.
Output: outputs/d01_d04_research_2026-10-28/lunar_impact_d01_d04_report.pdf.
The report adds interpretation and an explicitly proposed question ranking, not new measurements.
"""
from pathlib import Path
from html import escape
from copy import deepcopy
from io import BytesIO
import json
import math

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether, Image,
)
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs" / "d01_d04_research_2026-10-28" / "lunar_impact_d01_d04_report.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
M = json.loads((HERE / "model_results.json").read_text(encoding="utf-8"))
I = M["inputs"]
Q = M["base_photon_budget"]
LC = json.loads((HERE / "lightcurve_results.json").read_text(encoding="utf-8"))
EN = json.loads((HERE / "energy_distribution_results.json").read_text(encoding="utf-8"))
EX = LC["exponential_interpretation_only"]
EV = LC["ideal_event_example"]
FIG = ROOT / "figures" / "d01_d04_lightcurves"
rl_config.warnOnMissingFontGlyphs = 1
FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/liberation"), Path("/usr/share/fonts/liberation")]
LIBERATION = {"arial.ttf": "LiberationSans-Regular.ttf", "arialbd.ttf": "LiberationSans-Bold.ttf",
              "ariali.ttf": "LiberationSans-Italic.ttf", "arialbi.ttf": "LiberationSans-BoldItalic.ttf"}
def font_path(name):
    # Windows Arial when present; metric-compatible Liberation Sans on Linux (added 30 Oct 2026).
    for folder in FONT_DIRS:
        for candidate in (name, LIBERATION[name]):
            if (folder / candidate).exists():
                return str(folder / candidate)
    raise FileNotFoundError(name)
for family, name in [("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf"),
                     ("Arial-Italic", "ariali.ttf"), ("Arial-BoldItalic", "arialbi.ttf")]:
    pdfmetrics.registerFont(TTFont(family, font_path(name)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic")

PAGE_W, PAGE_H = A4
LEFT = RIGHT = 42
WIDTH = PAGE_W - LEFT - RIGHT
INK = colors.HexColor("#1D2B3E")
NAVY = colors.HexColor("#263F62")
MUTED = colors.HexColor("#526176")
PALE = colors.HexColor("#EEF2F6")
LINE = colors.HexColor("#CAD3DE")

styles = {
    "body": ParagraphStyle("body", fontName="Arial", fontSize=10.1, leading=13.3,
                           textColor=INK, spaceAfter=7, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="Arial", fontSize=9.1, leading=11.8,
                            textColor=MUTED, spaceAfter=6),
    "title": ParagraphStyle("title", fontName="Arial-Bold", fontSize=21, leading=25,
                            textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Arial", fontSize=12.3, leading=16,
                               textColor=MUTED, spaceAfter=7),
    "h1": ParagraphStyle("h1", fontName="Arial-Bold", fontSize=15, leading=19,
                         textColor=NAVY, spaceBefore=6, spaceAfter=9, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="Arial-Bold", fontSize=11.3, leading=14.6,
                         textColor=INK, spaceBefore=7, spaceAfter=6, keepWithNext=True),
    "cell": ParagraphStyle("cell", fontName="Arial", fontSize=9.35, leading=12.25,
                           textColor=INK),
    "cell_small": ParagraphStyle("cell_small", fontName="Arial", fontSize=8.95, leading=11.6,
                                 textColor=INK),
    "thead": ParagraphStyle("thead", fontName="Arial-Bold", fontSize=9.4, leading=12.2,
                            textColor=colors.white),
    "ref": ParagraphStyle("ref", fontName="Arial", fontSize=9.0, leading=11.9,
                          textColor=INK, spaceAfter=6),
    "formula": ParagraphStyle("formula", fontName="Arial", fontSize=10.0, leading=14.5,
                              textColor=INK, spaceAfter=2),
}


def p(text, style="body"):
    return Paragraph(text, styles[style])


story = []


def add(text, style="body"):
    story.append(p(text, style))


def heading(text, level=1):
    para = p(text, f"h{level}")
    if level == 1:
        para.outline_text = text
    story.append(para)


def data_table(headers, records, widths, small=False, padding=6):
    cell_style = "cell_small" if small else "cell"
    values = [[p(str(x), "thead") for x in headers]]
    values += [[p(str(x), cell_style) for x in row] for row in records]
    table = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
    ]))
    return table


def box(text):
    t = Table([[p(text)]], colWidths=[WIDTH])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def page():
    story.append(PageBreak())


def formula_box(lines):
    table = Table([[p(line, "formula")] for line in lines], colWidths=[WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PALE),
        ("BOX", (0,0), (-1,-1), 0.5, LINE),
        ("LEFTPADDING", (0,0), (-1,-1), 9),
        ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1,6))


def source_image(name, width):
    item = Image(str(FIG / name))
    item.drawHeight = item.imageHeight * width / item.imageWidth
    item.drawWidth = width
    return item


# PAGE 1 - Physical problem and comparison baseline.
add("Lunar impact-flash mission", "title")
add("D01-D04 research review", "subtitle")
add("Internal working report | 28 October 2026, review corrections 30 October | Values remain proposed", "small")
box("<b>Main finding.</b> The supply of photons is sufficient to justify further study of the proposed measurements. "
    "The main unresolved feasibility question is the calibrated response of the event camera to faint lunar flashes.")
heading("1 Introduction")
heading("1.1 Characteristics of lunar impact flashes", 2)
add("The Moon has no atmosphere, so impacts at tens of kilometres per second briefly heat gas and ejected material. "
    "This produces red visible and near-infrared flashes. Typical monitored events last tens to hundreds of milliseconds. "
    "A fast peak and a slower tail can trace different phases of the impact. Averaging the light over a camera exposure "
    "can hide the peak and bias its brightness.&nbsp;[1-3]")
add("The two-band measurements of NELIOTA place about 85% of the estimated peak temperatures between 2000 and 4500 K. "
    "These estimates depend on the emission model and the time sampling. In a study of 124 flashes by terrain, the fitted "
    "cooling times were 38 (+32/-18) ms for mare and 110 (+80/-50) ms for highlands. These are model parameters of average "
    "tails, not universal flash durations. [1,2]")
add("The measured light energy is only part of the impact energy. Converting light into impact energy or meteoroid mass "
    "also requires the fraction emitted as light, the impact speed and the emission geometry. More accurate light curves "
    "do not remove these unknowns by themselves. [10,14]")
heading("1.2 What measurement technologies can achieve", 2)
story.append(data_table(
    ["System / status", "Published capability", "Limit for this comparison"],
    [
        ["<b>NELIOTA</b><br/>Observed", "A 1.2 m telescope observes the R and I bands simultaneously, with 23 ms exposures and 10 ms readout. "
         "The practical limits are about R=11.2 and I=10.2 mag. [1]", "The limits vary with background and geometry. "
         "The reported 0.5° coordinate error is not a 95% surface error ellipse."],
        ["<b>Zadko</b><br/>Observed", "Four bright flashes were recorded at 200-250 frames/s, i.e. at 4-5 ms intervals. "
         "One fell by 1.5 mag within 4 ms. The 1.007 m telescope uses a long-pass filter starting near 715 nm. [3]", "The sample is small, "
         "two events are saturated and the calibration limits are acknowledged. It does not establish faint photometry at 1 ms."],
        ["<b>LUMIO</b><br/>Published design", "The aperture is 50.8 mm; an older analysis uses 15 frames/s and 66 ms exposures. "
         "The updated bands are 450-800 and 850-950 nm. Two channels support confirmation and temperature estimates. [4,5]", "These are planned farside "
         "measurements. ESA announced Phase C in March 2026; verifying the performance of the engineering model remains part of the development. [6]"],
        ["<b>Event cameras</b><br/>Device / laboratory", "Each pixel reports brightness changes independently. Sony quotes an IMX636 latency of "
         "≤100 µs at 1000 lx and ≤1000 µs at 5 lx. The fast-transient response can be calibrated in the laboratory. [7,8,12]", "Timestamp spacing "
         "does not show which light-curve detail can be recovered. Response speed, noise and absolute scale must be measured at the actual faint flux."],
    ], [87, 232, WIDTH-319], padding=5))
story.append(Spacer(1, 6))
add("A fair comparison uses equal wavelength bands, flash profiles, ranges, backgrounds and recovery criteria. "
    "Neither aperture nor apparent magnitude alone gives a fair ranking. [14]", "small")

# New introduction chapter: measured shapes, rather than one assumed template.
page()
heading("1.3 Flash light curves and added value")
heading("Observed shapes at 4-5 ms sampling", 2)
add("A light curve records brightness against time. The examples below show measured count rates before any conversion "
    "to absolute band flux. A sharp peak followed by a slower tail is common, but the early points, the secondary structure "
    "and the length of the tail differ. A single exponential fitted to every point is often inadequate. [3]")
panels = Table([[source_image("giancono_E1.png", (WIDTH-12)/2), source_image("giancono_E2.png", (WIDTH-12)/2)],
                [source_image("giancono_E3.png", (WIDTH-12)/2), source_image("giancono_E4.png", (WIDTH-12)/2)]],
               colWidths=[WIDTH/2, WIDTH/2], hAlign="LEFT")
panels.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                           ("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),
                           ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
story.append(panels)
add("<b>Figure A.</b> Four observed flashes from Giancono et al., author v1 p7 Fig. 5 [3]. The panels are cropped and rearranged; "
    "the data are unchanged. The horizontal axis is the time relative to the plotted peak (ms), and the vertical axis the count rate "
    "(electrons/s), with different scales. Red crosses mark saturated measurements. E4 includes a comparison at 50 frames/s through "
    "a different passband. Reproduced with attribution under CC BY 4.0.", "small")
story.append(data_table(
    ["Feature", "Published evidence", "What remains uncertain"],
    [
        ["Early peak", "E4 fades by 1.5 magnitudes in 4 ms, a factor of about four in flux. [3]",
         "The physical onset and the instantaneous peak can still be shorter than one exposure."],
        ["Different morphology", "E1 and E3 peak after the first recorded frame, and the authors report a secondary brightening in E3. [3]",
         "Four bright events do not establish occurrence rates or prove a unique physical cause."],
        ["Apparent duration", "E1-E4 are recorded for 20, 25, 85 and 20 ms. E2 and E3 saturate. [3]",
         "These detected durations depend on the threshold. Adaptive tail bins can be longer than 4-5 ms."],
    ], [94, 213, WIDTH-307], padding=5))
story.append(Spacer(1, 6))
add("<b>Selection matters.</b> The high-speed study requires at least two frames above a signal-to-noise ratio of 5 and a shape "
    "with a fast rise and slow decay. The NELIOTA terrain work selects multiframe flashes. Short, faint or unusual curves can "
    "therefore be underrepresented, and no universal shape, rise time or energy-duration law is established. [1-3,19]", "small")

page()
heading("1.3 Flash light curves (continued)")
heading("What is consistent, and where measurements can improve", 2)
story.append(source_image("terrain_Fig3.png", WIDTH))
add("<b>Figure B.</b> Average peak-normalized curves from Athanasopoulos et al., author v3 p3 Fig. 3 [2], "
    "with the I band on the left and the R band on the right. An increasing magnitude means fading. The shading is the reported "
    "scatter (rms), not the uncertainty of a universal template. Figure excerpt; data unchanged.", "small")
story.append(data_table(
    ["Result / model", "Published value", "Use for this concept"],
    [
        ["Single-size cooling fit", "Mare: 38 (+32/-18) ms.<br/>Highland: 110 (+80/-50) ms. [2]",
         "The terrain averages diverge from about 50 ms after the peak. Accurate tails and reliable terrain labels are useful science."],
        ["Two-size cooling fit", "A slow component has a fitted cooling parameter of about 0.5 (+0.3/-0.3) s. [2]",
         "Mixed and persistent tails should be tested. These physical-model parameters are not universal exponential constants."],
        ["Spectral evolution", "Some initial spectra favour components of roughly 2000 K + 6000 K, sampled every 16/25 ms. [18]",
         "Single-band data cannot separate these components uniquely. The 600-900 nm trial band misses the excess below ~600 nm."],
    ], [112, 182, WIDTH-294], padding=5))
heading("Three places where refined curves could add value", 2)
add("<b>Early light, approximately the first 20 ms.</b> Here we can test the peak width, delayed peaks and the ratio of early "
    "to total band energy. A calibrated 1 ms product could improve on the observed 4-5 ms sampling. It would not by itself resolve "
    "the sub-ms vapour phase suggested by impact models or by microsecond laboratory flashes. [3]")
add("<b>Later light, from tens of ms to seconds.</b> Here we can measure cooling, secondary peaks and the energy below older "
    "detection thresholds. The terrain study discusses up to ~30% more light at equal peak brightness, and an uncertainty of 10% "
    "in the integrated band energy is a useful trial target for this comparison. One exceptional flash in 2013 lasted 8.3 s and "
    "faded by about five magnitudes in its first 0.25 s, so adaptive recording is preferable to a universal cut-off at 100 ms. [2,17]")
add("<b>Comparisons between populations.</b> Band, peak definition, background and sensitivity must be matched before "
    "terrains or hemispheres are compared. The uncertainties of individual curves and the selection efficiency, including rejected "
    "shapes, should be reported. Better flux estimates need these corrections as well as more detections. Independent constraints "
    "from craters and impacts remain necessary to test the conversion from measured light to impact energy. [1,2,10,19]")

# New introduction chapter: reconstruction inputs and limits.
page()
heading("1.4 Reconstructing a calibrated light curve")
heading("From conventional frames", 2)
add("<b>1.</b> The raw images are corrected for offset, dark signal, pixel response and gain. They are then registered, the "
    "shape of the point source is measured, and the nearby lunar background is subtracted. The signal is summed within a "
    "calibrated aperture or fitted with that shape. [1,3,20]")
add("<b>2.</b> The signal is converted to received band flux using reference sources and the wavelength response of the "
    "instrument. Ground observations also need atmospheric corrections. The colour of a star can differ from the changing "
    "spectrum of a flash. [14,20]")
add("<b>3.</b> The actual start and end times of each exposure, the gaps and the saturation flags are kept, because each datum "
    "is a time average. The measured energy is the sum of flux multiplied by exposure duration. Filling missing intervals with a "
    "fitted tail adds a model-dependent contribution and uncertainty; it does not recover a uniquely measured peak. [3,21]")
formula_box([
    "C<sub>j</sub> = K × ∫<sub>exposure j</sub> [F<sub>B</sub>(t) + B<sub>B</sub>(t)] dt + noise",
    "H<sub>B</sub> = Σ F̄<sub>B,j</sub> Δt<sub>j</sub> + explicitly modelled missing contributions",
])
add("C is the corrected signal of source plus background, and K is the calibrated conversion for the stated response and spectrum. "
    "F<sub>B</sub> is the flash flux in the band, B<sub>B</sub> the background and H<sub>B</sub> the received radiant exposure. "
    "The unknown curve between samples requires assumptions.", "small")
heading("From an event camera", 2)
formula_box([
    "L<sub>p</sub>(t) ≈ L<sub>p</sub>(t<sub>0</sub>) + Σ<sub>events at p</sub> s<sub>k</sub> c<sub>p,s</sub>;  I<sub>p</sub>(t) = exp[L<sub>p</sub>(t)]",
    "c<sub>ON</sub> = ln(1 + θ<sub>ON</sub>);  c<sub>OFF</sub> = -ln(1 - θ<sub>OFF</sub>)",
])
add("Here p is a pixel, s is +1 or -1 for ON or OFF events, and c is the calibrated logarithmic threshold. This ideal approximation "
    "describes the <b>total pixel intensity, including background</b>, after the finite response of the sensor. Event timing, "
    "bandwidth, threshold mismatch and missed events must enter the real model. Integrating changes alone leaves the initial "
    "absolute intensity undetermined. [7,8,15]")
story.append(data_table(
    ["Required input", "Why it is needed"],
    [
        ["Absolute intensity/background anchor", "It sets the scale before the flash is subtracted. A calibrated local reference or a validated alternative is needed."],
        ["Pixel and optical calibration", "ON/OFF thresholds; response versus flux and temperature; wavelength response, source footprint, gain and noise."],
        ["Timing and completeness", "Calibration of clock and latency; relative timing of a reference channel; records of refractory periods, saturation and dropped events."],
    ], [169, WIDTH-169], padding=5))
story.append(Spacer(1, 6))
add("<b>Candidate mission method.</b> We would fit the source flux directly over its pixel footprint, with finite-rise, "
    "flexible-tail and secondary-peak alternatives. The calibrated sensor model predicts the event crossings, which are compared "
    "with the observed events and quiet intervals. Any intensity reference is fused according to its uncertainty. Complementary "
    "and Kalman filters are starting methods, but their priors and noise models must be tested on held-out point flashes. A "
    "reconstructed video is optional; the scientific product is a band-flux curve with valid uncertainties. [8,15,16]")

page()
heading("1.4 Reconstruction (continued)")
heading("What accuracy is established today?", 2)
story.append(data_table(
    ["Evidence", "Quantitative result", "What the number does not establish"],
    [
        ["Conventional fast photometry", "E4 is quoted at ±0.07 mag, about ±6.4% in flux for its averaged peak of ~3.8 ms. [3]",
         "The study acknowledges limits of the absolute calibration. Saturated and instantaneous peaks remain uncertain."],
        ["Complementary fusion", "Image errors of 7.76±0.49% / 9.05±1.19%, with synthetic events from 168 Hz video and 20 Hz reference frames. [15]",
         "These image metrics do not certify the energy or peak accuracy for an unresolved source at 1 ms."],
        ["Later Kalman fusion", "A 69.4% relative reduction in absolute image-intensity error compared with other methods. [16]",
         "A relative improvement of an algorithm is not an absolute percentage flux uncertainty."],
        ["Event astronomy", "Measured brightness comparisons use 100-500 ms bins; simple event-rate models differ by factors of 10-100. [9]",
         "This is a promising calibration route, but there is no demonstrated error bound for faint lunar flashes at 1 ms."],
        ["Fast-transient calibration", "EVK4: corners of 1-11 kHz and refractory periods of 12-480 µs across settings. [8]",
         "These response parameters are specific to device and illumination; they do not guarantee reconstructed-flash accuracy."],
    ], [102, 220, WIDTH-322], small=True, padding=5))
heading("Specific targets for further analysis", 2)
add("<b>Peak averaging.</b> If the 1.5-magnitude fall in 4 ms is read as a pure exponential, τ≈2.895 ms. "
    "For an exposure aligned with the onset, mean/initial peak = (τ/Δt)[1-exp(-Δt/τ)]. This is an analytic illustration, "
    "not a fit to the raw E4 data or a universal flash shape.", "small")
means = {x["bin_ms"]:x["mean_over_initial_peak"] for x in EX["averaged_peak_fractions"]}
story.append(data_table(
    ["Average width", "0.25 ms", "1 ms", "5 ms", "23 ms", "66 ms"],
    [["Mean / initial peak", *[f"{means[b]:.3f}" for b in [0.25,1.0,5.0,23.0,66.0]]]],
    [121, *[(WIDTH-121)/5]*5], padding=5))
story.append(Spacer(1, 6))
add("An exposure of <b>≤0.30 ms</b> would limit the averaging loss of this example to 5%; we treat this as a stretch test for "
    "a brighter subset. We keep the present <b>1 ms / 10⁴ J</b> and <b>5 ms / 3×10³ J</b> candidates with their explicitly "
    "averaged peak definition, because shorter bins need a new joint budget of photons and response.", "small")
add("<b>Event calibration.</b> At a representative ON threshold of 12%, a 10:1 rise spans about <b>20 events/pixel</b>. "
    "A log-uniform rise over 1 ms then needs a refractory period below roughly <b>49 µs</b> just to avoid this rate limit. "
    "One missed ON event makes the reconstructed total intensity <b>10.7% too low</b>, and background subtraction can amplify "
    "the flash error. A coherent threshold error of about <b>2.1%</b> alone causes a 5% intensity error over this rise. "
    "These are ideal sensitivities to be tested, not achieved tolerances.", "small")
add("<b>Further trial allocations.</b> The unrecorded band energy should be bounded to <b>≤2%</b> or flagged, and this should be "
    "reviewed within the D03 budget. We keep adaptive multi-second tails and trial a <b>200 ms raw pretrigger</b> store for the "
    "100 ms detector window. If two bands are used, a <b>≤0.1 ms relative offset</b> should be tested (~3.5% ratio error for the "
    "exponential above). A separate 1 kHz sine test needs a first-order corner of ≥3.04 kHz for ≤5% uncorrected amplitude loss. "
    "All response limits must be measured at the actual faint irradiance, and none replaces joint pulse-recovery tests.", "small")
add("The new Light curves and Reconstruction worksheets keep the source conditions, required inputs, derived values and "
    "tests LCT01-LCT08. In this study we did not re-reduce raw telescope data or perform a calibrated reconstruction with a "
    "lunar event camera.", "small")

# The observed energy population and the limitations of inferring all impacts.
page()
heading("1.5 Impact energies: range and distribution")
add("<b>What is measured?</b> A flash supplies calibrated light in an instrument band. The kinetic impact energy is inferred as "
    "<b>K = E<sub>light</sub>/η</b>, where η is the assumed fraction emitted in that band and angular convention. "
    "The mass additionally needs the speed: <b>m = 2K/v²</b>. Different bands, peak-frame versus whole-flash integration "
    "and the assumed η prevent published energy limits from being pooled directly. [1,22,23]")
story.append(data_table(
    ["Verified example", "Optical observation", "Inferred impact energy and limits"],
    [
        ["<b>Smallest in the compiled calibrated sample</b><br/>NELIOTA #111", "R+I ≈<b>4200 J</b>; source values R=2000±600 J, I=2200±300 J. [22]",
         "<b>2.8 MJ</b> from the rounded light at η=0.0015; the table quotes 3±1 MJ. The same light gives 0.84-8.4 MJ for η=0.005-0.0005. This is a catalogue extreme, not a proven all-time minimum."],
        ["<b>Recorded optical range</b><br/>192 validated NELIOTA events", "<b>4200-580,000 J</b> integrated R+I. Median <b>21,000 J</b>; middle half ≈14,000-52,500 J. [1,22]",
         "The published tables at nominal η span <b>3-388 MJ</b>. Both endpoints and the distribution are selected observations; no complete energy interval is established."],
        ["<b>Strongest recorded flash in the reviewed literature</b><br/>11 September 2013", "V=2.9±0.2 mag; 8.3 s. Optical energy in the source convention ≈<b>1.3×10⁸ J</b>, derived from Kη. [17,29]",
         "<b>(6.5±1.0)×10<super>10</super> J</b> at η=0.002 (~15.6 t TNT). The quoted error does not span the η uncertainty. The 2025/2026 crater paper still identifies this optical record."],
        ["<b>Largest contemporary crater found</b><br/>McGetchin, formed in 2024", "A <b>222 m</b> crater found in before/after images; this record has no calibrated flash measurement. [24]",
         "<b>6.5×10¹³ J</b> from crater scaling at 15 km/s and 3 g/cm³. This is a different inference with no quoted energy confidence interval; it is not an optical record or a physical upper cutoff."],
    ], [112, 177, WIDTH-289], small=True, padding=5))
story.append(Spacer(1, 5))
story.append(Image(str(ROOT / "figures/lunar_impact_energy/neliota_energy_distribution.png"), width=WIDTH, height=WIDTH*0.42))
add("<b>Figure C.</b> Reproduced analysis of 79+113 published rows of validated flashes, not new observations. Left: counts "
    "in unequal bins of optical energy (27,88,53,15,9). Right: cumulative fraction at or above each energy under three common η "
    "assumptions. The curves are scenario shifts, not confidence bounds or a completeness-corrected flux. K is calculated "
    "consistently from the rounded R+I values. R+I is not the provisional 600-900 nm top-hat band of the mission. [1,22]", "small")
add("<b>The complete intrinsic distribution is not known.</b> More small than large impactors are expected, but the drop at the faint "
    "end of this catalogue mixes the population with missed flashes. No universal power law, physical minimum or maximum follows. "
    "The full event rows, source pages and uncertainties are kept in the workbook and CSV. The narrative maximum of 2024 "
    "(1.05 GJ across η scenarios, Fig. 23 discussion) differs from the retained table maximum of 2020 (1.164 GJ); it may reflect a different sample or velocity convention. Neither is a fixed-η range.", "small")

page()
heading("1.6 What is missed, and where uncertainty remains")
add("<b>Smaller impacts exist below the limits of optical surveys.</b> LADEE/LDEX measured a dust cloud generated by impacts; its "
    "~0.3 µm threshold describes <i>secondary ejecta</i>, not the incoming impactor. NASA's MEM3 models particles of 10<super>-6</super>-10 g. "
    "A particle of 10<super>-6</super> g at an assumed 20 km/s carries just <b>0.2 J</b>. This is an illustrative calculation, not a "
    "measured lunar flash or a physical lower cutoff, and the optical signal can be far too faint to detect. [25,26]")
add("<b>How a population is reconstructed.</b> For each interval of energy, position and time, we predict the incoming impacts, "
    "their emission and the measured data, and apply the same detection and confirmation cuts as the catalogue. The predicted counts "
    "are compared with the observations using the measured recovery probability p<sub>det</sub> and the observed surface area-time. "
    "Energy errors and η scenarios stay in this inference. A simple bin estimate N/(area×time×p<sub>det</sub>) works only when "
    "those terms represent that bin, and the corrections become unstable where recovery is poorly known or near zero.")
story.append(data_table(
    ["Uncertainty", "Quantitative evidence / limitation", "Consequence for this mission"],
    [
        ["Energy and missing light", "η=0.0005-0.005 shifts the inferred K by a factor of <b>10</b> for unchanged light. Frame gaps, "
         "clipped peaks and unrecorded tails add separate errors. [1,21,22]", "Report the received exposure and band energy first; "
         "a ≤10% optical-energy target is not a ≤10% kinetic-energy measurement."],
        ["Within-flash timing", "NELIOTA integrates 23 ms with a 10 ms gap per ~33 ms. The ideal live fraction is 69.7%, and a 1 ms pulse "
         "can lie wholly in a gap for 27.3% of random onset phases, before other losses.", "This is an illustrative gap calculation, "
         "not a measured completeness. Event pixels still need calibration of faint-light response and losses."],
        ["Event epoch and location", "2013 flash: reported detection epoch ±0.01 s and coordinates ±0.2° (~6.1 km meridional arc). "
         "NELIOTA quotes 0.5° (~15.2 km) without a stated confidence level. [1,17,29]", "Keep the absolute epoch, resolved structure "
         "and location confidence separate. Retain the D02/D04 candidates and the light-time correction."],
        ["Crater timing / mapping", "The occurrence bracket for McGetchin is <b>41 days</b>; the terrain model has 3 m/pixel and &lt;1.5 m vertical "
         "precision. These do not establish a horizontal 95% error region. [24]", "Crater observations may locate a missed large "
         "event accurately, but they cannot reconstruct its millisecond light curve."],
        ["Survey time and sampling", "NELIOTA had <b>283.4 h</b> of usable exposure in 6.5 years (~0.50% of the elapsed calendar time) and "
         "an approximate field area of 3.11×10⁶ km² (~8.2% of the Moon). Neither is a global effective exposure. [1]", "Record the area-time by "
         "energy, location, illumination and season. Later revisits cannot recover missed events."],
        ["Space/time population", "Published sporadic/stream rates are 1.96/3.32×10<super>-7</super> km<super>-2</super> h<super>-1</super>, from 145/47 events. The ratio is ~1.69, "
         "with a counting-only relative uncertainty of ~17%. Small-particle models predict directional and seasonal structure. [1,27]", "These "
         "are selected flash rates, not all-impact rates. Comparisons of near and far side, poles and terrain need matched selection and timing."],
    ], [85, 223, WIDTH-308], small=True, padding=5))
add("<b>Spatial evidence has a time scale.</b> The Chang'E-6 work on soil and craters supports a similar small-impact flux on the "
    "near and far side over <b>million-year</b> intervals; it is not a contemporary survey of the poles or of flash energies. [28] "
    "Apparent flash hotspots also mix exposure, terrain emission and detection. The model prediction of one largest crater every "
    "132 years cannot be calibrated from one event. [24]", "small")
add("<b>Further-analysis targets, all provisional.</b> Inject 10²,3×10²,10³,3×10³,10⁴,3×10⁴,10⁵,3×10⁵,10⁶ J "
    "in the mission band, and find the energies with 50/90/95% end-to-end recovery and the bright-end loss across shapes and spectra. "
    "For population comparisons, test ≤5% relative recovery and ≤5% area-time uncertainty. Two equally populated bins need ~<b>200 "
    "complete independent events each</b> for a 10% counting error on their rate ratio, and ~450 each for a local 3σ test of a 20% "
    "difference, before systematics. No new D01-D04 threshold or mission lifetime is selected.", "small")

# Original research priorities and the mission-level drivers.
page()
heading("1 Introduction (continued)")
heading("1.7 Open questions ranked for concept development", 2)
add("This proposed ordering reflects the added value and the dependencies for concept development. As requested, flash "
    "physics and impact counts remain alternatives of equal priority.")
story.append(data_table(
    ["Rank", "Open question", "Why answering it adds value"],
    [
        ["<b>1</b>", "Can event data provide calibrated 1-5 ms light curves at useful faint-flash levels?", "This decides "
         "whether the sensing premise offers a measurable gain. Absolute brightness, response speed, lost events and false detections "
         "must be solved together. Laboratory and star/satellite results are useful leads, not a lunar validation. [7-9,12,13]"],
        ["<b>2a</b>", "How do the early peak and the later cooling depend on terrain and impact conditions?", "Fine, calibrated "
         "profiles could separate rapid and persistent emission, test cooling models and reduce the bias from time sampling. The existing "
         "terrain differences give a concrete comparison, but their physical cause is not settled. [2,3]"],
        ["<b>2b</b>", "Does the impact rate vary between hemispheres, polar regions or terrain types?", "A catalogue with controlled "
         "exposure could separate real spatial differences from missed faint events and from illumination and terrain biases. It needs a "
         "known observed area, observing time and detection efficiency, not just more detections. [1,4]"],
        ["<b>3</b>", "Can flash measurements improve estimates of impact energy and mass?", "Craters linked to flashes can constrain "
         "the conversion from light to impact energy. The remaining dependence on crater laws, band, speed and terrain must be tested, "
         "and accurate locations make these checks practical. [10,11]"],
        ["<b>4</b>", "Would faster colour measurements justify another spectral channel?", "Temperature measurements already "
         "exist. Added value would come from better time-resolved colour or a demonstrated benefit for calibration or confirmation. "
         "A second channel also divides the photons and increases the calibration work. [1,5,14]"],
    ], [38, 177, WIDTH-215], padding=6))
heading("1.8 Why D01-D04 matter", 2)
story.append(data_table(
    ["Driver", "Measurement it controls", "Consequence for the design"],
    [
        ["<b>D01</b><br/>Sensitivity", "Which faint flashes enter the catalogue, and how often comparable flashes are missed.",
         "Light-collecting diameter, allowed range, background control and detection processing."],
        ["<b>D02</b><br/>Time recording", "Which changes in a flash can be recovered, and how accurately the time is known.",
         "Pixel response speed, clock, readout capacity and buffering."],
        ["<b>D03</b><br/>Photometry", "Accuracy of the peak brightness and light energy in a defined wavelength band.",
         "Absolute calibration, an intensity reference if needed, thermal stability and loss accounting."],
        ["<b>D04</b><br/>Location", "Whether an event can be assigned to a terrain or used for a crater search.",
         "Angular sampling, camera alignment, pointing knowledge, orbit knowledge and surface mapping."],
    ], [70, 210, WIDTH-280], padding=5))
story.append(Spacer(1, 7))
add("A detected flash does not automatically satisfy D02-D04. The catalogue should state which events also meet "
    "the quality in time, brightness and location that a particular scientific use needs.")

# PAGE 3 - Reproducible assumptions and methods.
page()
heading("2 Methodology")
heading("2.1 Reference assumptions", 2)
add("The extended study reviewed 39 evidence records and followed primary papers, device documents and agency updates. "
    "We kept observed results, planned designs, study assumptions and proposed targets separate. The reference case below "
    "tests physical plausibility; it does not select a spacecraft or payload.")
story.append(data_table(
    ["Item", "Assumption used", "Why it was used / limitation"],
    [
        ["Spectrum / band", "A 3000 K thermal-emission model (blackbody) and a uniform analysis band of 600-900 nm.", "A representative red flash spectrum. "
         "Real filter and detector response curves must replace this simplified band. [1,14]"],
        ["Flash / timing", "Instantaneous onset and exponential decay with a 100 ms time constant; 100 ms detection window; "
         "1 s background reference.", "An explicit, repeatable profile. It cannot validate the recovery of rise times or all real light curves. "
         "A 100 ms window captures 63.2% of the total energy of this profile."],
        ["Optics / detector", "200 mm aperture, 500 mm focal length; 30% effective photon-to-charge fraction; noise footprint of nine pixels; "
         "4.86 µm pixels, 1280 × 720 array.", "A sizing example, not a measured IMX636 efficiency. The 30% includes optical, detector, "
         "image-spread and any channel-splitting losses. The pixel geometry follows [12]."],
        ["Range / background", "Flash-to-spacecraft range of 50,000 km; background band brightness "
         "L<sub>B</sub>=10<super>-3</super> W/m²/sr; background photon conversion at 750 nm.", "Both are study inputs. The background "
         "is not a measured R/I-to-broadband conversion or a complete stray-light model."],
        ["Location errors", "Flash centre 0.2 pixel; attitude 0.5 arcsec; camera alignment 0.3 arcsec; residual pointing motion "
         "0.2 arcsec; orbit, horizontal map and height errors 50 m each.", "All are assumed one-standard-deviation errors, independent "
         "and Gaussian. An arcsec is 1/3600 degree. Correlations and bias need further work."],
        ["Mission scope", "Both hemispheres and the poles over time; illumination and exclusions cannot exempt any region (28 Oct scope). Supporting systems are permitted only "
         "where necessary. No fixed platform, lifetime or architecture.", "Both science priorities and both location outcomes remain open. "
         "Independent versus ground-cooperative global coverage is unresolved."],
    ], [84, 224, WIDTH-308], small=True, padding=4))  # 2 Nov 2026 restyle: 5 -> 4 keeps 14 pages
heading("2.2 Analysis performed", 2)
add("<b>Photon budget.</b> The received light energy per collecting area is H<sub>B</sub>. The bookkeeping energy "
    "Eeq assumes that the same observed brightness radiates uniformly into a hemisphere. It is defined by:")
formula_box([
    "H<sub>B</sub> = Eeq / (2πr²)",
    "Total signal = H<sub>B</sub> × collecting area × 0.30 × photons per joule",
    "SNR = window signal / √[window signal + B × (1 + t / t_ref)]",
])
add("Here r is the range, B the background charge in the window t, and t<sub>ref</sub> the independent baseline interval. "
    "SNR is the signal-to-noise ratio. The model spectrum gives 3.85 × 10<super>18</super> photons/J in the analysis band. "
    "The calculation includes photon noise and the noise of the baseline estimate. Charge counts are not event counts of an event camera. "
    "A provisional approximation for 90% recovery uses a required SNR of 9.28; real recovery and false-confirmation rates need tests.", "small")
add("<b>Trades and curve examples.</b> The 54-case CSV varies range, aperture, background and decay time and records all inputs. "
    "Separate brightness allowances and a local propagation of surface errors test consistency, and a multiplier of 2.45 gives "
    "the 95% ellipse. The analytic curve examples integrate an exponential aligned with the onset and propagate log-event increments "
    "and a first-order response. Published reconstruction benchmarks supply comparison cases. These calculations do not fit raw "
    "observations or recover missing measurements.", "small")
add("<b>Energy catalogue.</b> We extracted 192 validated rows with source pages, tokens and errors, and checked the units and η "
    "conversions. The histograms describe selected observations without completeness correction. The stream labels give 146/46, "
    "against 145/47 in the published rates; both are kept. No new measurement, calibrated v2e run or orbit analysis was performed.", "small")

# PAGE 4 - The candidate answers and their derivation.
page()
heading("3 Results")
heading("3.1 Candidate answers and why they were chosen", 2)
add("The literature establishes useful comparisons and shows where evidence is missing, but it does not prescribe one unique set of "
    "mission values. The answers below are rounded trial targets for science and engineering under the reference conditions in §2.1.")
story.append(data_table(
    ["Driver", "Candidate answer", "How the value was selected"],
    [
        ["<b>D01</b>", "<b>Exposure at 90% recovery ≤6.4 × 10<super>-14</super> J/m²</b>, equivalent to a limiting "
         "<b>Eeq ≤1000 J</b> at 50,000 km. Target <b>≤0.01 false confirmed flashes/h/spacecraft</b>.",
         "1000 J is a useful sizing trial, not a uniquely derived science cutoff. The ideal model gives SNR≈21 and a Gaussian detection "
         "proxy of roughly 400 J, but the actual sensor response may consume this headroom. The recovery and false-rate values are proposed "
         "allocations for catalogue quality."],
        ["<b>D02</b>", "Keep two characterization options:<br/><b>3000 J / 5 ms</b>, rise/decay error <b>≤2.5 ms RMS</b>;<br/>"
         "<b>10,000 J / 1 ms</b>, error <b>≤0.5 ms RMS</b>.<br/>Absolute lunar emission time: <b>≤0.1 ms at 95%</b>.",
         "The chosen pairs of energy and bin give comparable photon statistics, about 6-7% random peak error. The 1 ms option would resolve "
         "finer detail than the observed 4-5 ms ground benchmark [3]. At 50,000 km, however, the realistic pixel illuminance (~0.02-0.2 lx) is far below Sony's 5 lx specification point, so current sensor evidence does not support it. The time-error allocations are half the target feature width, and the absolute "
         "time allowance is one tenth of 1 ms."],
        ["<b>D03</b>", "For characterized events: standard uncertainty <b>≤10% in band energy</b> and <b>≤20% in peak band flux</b>, "
         "with a residual mean bias of <b>≤5%</b> for each. The peak is the brightest <b>1 or 5 ms average</b> of the selected option.",
         "Errors below the reported ~30% terrain effect on energy at the same peak help to preserve scientific differences. [2] The proposed "
         "independent allowances total 9.7% for energy and 19.6% for peak flux. These are allocations to be demonstrated, not measured "
         "uncertainties, and the unresolved event-reconstruction terms are consequential."],
        ["<b>D04</b>", "Keep a <b>95% ellipse semimajor ≤5 km</b> for terrain catalogues, or <b>≤1 km</b> for practical crater searches. "
         "The semimajor is the longest distance from centre to edge. For terrain assignment, <b>≥95% of the region's area</b> must lie in one class.",
         "5 km is a trial scale finer than the ~15 km coordinate arc of NELIOTA; it is not a universal terrain-resolution requirement. "
         "A 1 km semimajor limits the enclosing search diameter to 2 km, which is useful within the nominal ~5 km swath of an LROC NAC pair. "
         "Suitable before/after images are still needed. [1,2,11]"],
    ], [41, 244, WIDTH-285], small=True, padding=6))
story.append(Spacer(1, 7))
add("<b>Acceptance definitions.</b> RMS describes the size of the error across repeated tests. A standard uncertainty is approximately "
    "a one-standard-deviation estimate, not a 95% bound, and bias is the mean systematic offset. Time recovery should be tested with "
    "finite-width features at least 50% brighter than the underlying flash, using an independent fast reference.", "small")
heading("3.2 Worked photon result", 2)
survey_signal = Q["source_electrons_total"] * 3 * (1-math.exp(-5/I["decay_constant_ms"]))
survey_b = Q["background_electrons_s"] * 0.005
survey_snr = survey_signal/math.sqrt(survey_signal+survey_b+Q["background_electrons_s"]*0.005**2)
story.append(data_table(
    ["Reference-model quantity", "1000 J detection", "3000 J survey", "10,000 J physics"],
    [
        ["Integration / averaging interval", "100 ms", "5 ms", "1 ms"],
        ["Source charge equivalent (photoelectrons)", f"{Q['source_electrons_window']:,.0f}", f"{survey_signal:,.0f}", f"{Q['characterization_electrons_peak_bin']:,.0f}"],
        ["SNR from photon/background statistics", f"{Q['snr_detection']:.1f}", f"{survey_snr:.1f}", f"{Q['snr_characterization_peak_bin']:.1f}"],
    ], [215, 100, 98, WIDTH-413], padding=5))
story.append(Spacer(1, 6))
add("The peak bins are optimistically aligned with the onset. The model does not prove the proposed recovery probability, time "
    "resolution or absolute photometry, and a 90% detection target does not establish a 95%-complete catalogue.", "small")

# PAGE 5 - Interpret the bounds and state the concept-development sequence.
page()
heading("3 Results (continued)")
heading("3.3 Error allowances and viewing geometry", 2)
left_table = data_table(
    ["Proposed allowance", "Energy", "Peak"],
    [
        ["Photon + background statistics", "7%", "16%"],
        ["Absolute brightness calibration", "5%", "5%"],
        ["Event reconstruction / losses", "4%", "10%"],
        ["Drift / remaining background", "2%", "2%"],
        ["Range conversion", "1%", "1%"],
        ["<b>Combined, if independent</b>", f"<b>{100*M['energy_rss_fraction']:.1f}%</b>", f"<b>{100*M['peak_rss_fraction']:.1f}%</b>"],
    ], [162, 50, 43], small=True, padding=3)
right_table = data_table(
    ["Viewing angle*", "95% semimajor"],
    [[f"{r['emission_deg']}°", f"{r['major95_km']:.2f} km"] for r in M["localization"]],
    [103, WIDTH-255-14-103], small=True, padding=3)
side = Table([[left_table, "", right_table]], colWidths=[255,14,WIDTH-269], hAlign="LEFT")
side.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                          ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                          ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
story.append(side)
story.append(Spacer(1, 6))
add("*Angle from the local surface normal; 0° is straight down. The assumed location budget meets the 1 km candidate at 60° "
    "but misses it at 70°. The 95% coverage of real errors still needs validation. The poles require local surface coordinates, and "
    "near the limb a full model of camera ray and surface must replace this approximation.", "small")
add("The brightness allowances are combined by squaring, summing and taking the square root. Correlated errors and mean bias need "
    "separate treatment. The budget covers the defined band and the Eeq convention, not the uncertain angular emission or the conversion to mass.", "small")
heading("3.4 Additional insights", 2)
add("<b>Range and coverage are coupled.</b> The same target for received exposure corresponds to <b>40 / 1000 / 2560 J</b> at "
    "<b>10,000 / 50,000 / 80,000 km</b>. The example field is only <b>0.71° × 0.40°</b>. Higher measurement quality in one field "
    "does not provide enough observing area or a large enough global sample, and a later revisit cannot recover a missed flash.")
add("<b>Supporting references solve a specific problem.</b> Ideal event pixels measure relative changes and need an absolute "
    "intensity anchor. Ground calibration and simultaneous nearside observations can help, but they do not directly reference unobserved "
    "farside flashes. An onboard intensity reference or a validated event-only method may therefore be needed. Neither automatically fixes "
    "the slow response to faint light. [7-9,12,13]")
add("<b>Timing and counts need explicit corrections.</b> At 50,000 km, the light reaches the spacecraft about <b>166.8 ms</b> after "
    "emission. Roughly <b>100 independent, fully recovered events</b> give a 10% uncertainty for one count, and a ratio of two equal "
    "counts needs ~200 each. Optical-energy distributions should be kept separate from uncertain kinetic scenarios (§§1.5-1.6). "
    "Neither the lifetime nor the number of spacecraft is established.")
heading("4 Conclusion")
add("The mission should be evaluated on calibrated fast-flash measurements and on impact counts corrected for exposure. LUMIO already "
    "targets farside access, so access alone does not establish added value. Platform size and orbit should follow the validated payload "
    "and the usable exposure. The examples support further design work, but the joint faint-flash performance of the selected sensor remains unproven.")
heading("Next steps for the team", 2)
for text in [
    "<b>1. Validate the measurement chain.</b> Test faint pulses across background, temperature and settings. Start with spectra "
    "equivalent to 2000-4500 K, trial mixtures of 2000/6000 K and profiles of 1-1000 ms, and extend to multi-second tails. Include delayed "
    "and secondary peaks and an unknown bin phase. Measure recovery, false detections, time errors, photometry and event loss together.",
    "<b>2. Compare support options.</b> Determine whether an event-only method, ground assistance or an onboard reference meets the "
    "required calibration and confirmation needs, including environmental stability and the cost in throughput.",
    "<b>3. Trade architectures using usable data.</b> Compare both science priorities and location outcomes with the actual observed area-time, "
    "range and energy-dependent sample counts. Measure completeness, seasonal and polar exposure and bright-end losses, and "
    "resolve independent versus ground-cooperative global coverage.",
    "<b>4. Select and baseline values.</b> Agree on the evidence needed for added value, compare matched conditions with ground systems and "
    "LUMIO, and then set requirements and subsystem budgets with margins.",
]:
    add(text, "small")

# PAGE 6 - Short source index, exact locators and reproducibility trail.
page()
heading("Sources and verification trail")
add("Numbers in brackets identify the sources below. The E identifiers map to the Evidence sheet of the D01-D04 workbook. "
    "When checking a result, use the stated manuscript version and page, because the journal pagination may differ.", "small")
references = [
    (1,"Liakos et al. (2024), NELIOTA updated results, A&amp;A 687 A14.",
     "Author PDF v1 pp2-4, §§4,6-7, Table 2; pp19-21 Table A.2. E03.","https://arxiv.org/pdf/2403.19613v1","Author PDF"),
    (2,"Athanasopoulos et al. (2026), Mare versus highland flash light curves, A&amp;A 710 L29.",
     "Author PDF v3 pp2-4, Fig. 3, Table C.1. E04.","https://arxiv.org/pdf/2605.19635v3","Author PDF"),
    (3,"Giancono et al. (2026), High-speed observations of lunar impact flashes, PASA 43 e098.",
     "Publisher §§3-5, Table 2, Figs 5-6; author v1 pp4-9,13-14. E05. Publication/full HTML verified; Figure A uses author-v1 Fig. 5.",
     "https://doi.org/10.1017/pasa.2026.10211","Publisher paper"),
    (4,"Topputo et al. (2023), Meteoroids detection with the LUMIO lunar CubeSat, Icarus 389, 115213.",
     "Supplied PDF p5 Table 4 and pp6-13. Phase A model. E09.","https://doi.org/10.1016/j.icarus.2022.115213","DOI"),
    (5,"Pancalli et al. (2024), LUMIO payload design, IAC-24 B4.8.5 x84906.",
     "PDF pp2-3, Tables 1-3. E10. Web PDF text checked; local download blocked.",
     "https://re.public.polimi.it/retrieve/f609816c-3cf5-4468-93bc-12ee09e38135/PANCM01-24.pdf","Primary paper"),
    (6,"ESA (27 March 2026), A leap forward for Lumio: Phase C officially launched.",
     "In brief; What is next in Phase C? Rechecked 28 October 2026. E11.",
     "https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/A_leap_forward_for_Lumio_Phase_C_officially_launched","Agency update"),
    (7,"Gallego et al. (2022), Event-based Vision: A Survey, TPAMI 44, 154-180.",
     "Supplied PDF p3; §§4.6,6.2 (pp17-18,23). E12.","https://doi.org/10.1109/TPAMI.2020.3008413","DOI"),
    (8,"Pedersen et al. (2026), Event-camera calibration for fast luminous events, Remote Sensing 18, 3201.",
     "§§4-5, Figs 2,3,9. E14. Device/illumination-specific laboratory results.","https://doi.org/10.3390/rs18183201","Publisher paper"),
    (9,"Benson and Holzinger (2025), Event Camera Photometry for Non-Resolved Objects, AMOS.",
     "PDF pp1-5,11. E13. Star/satellite regimes do not validate lunar millisecond photometry.",
     "https://amostech.com/TechnicalPapers/2025/Satellite-Characterization/Benson.pdf","Conference paper"),
    (10,"Sheward et al. (2025), Detection of small fresh craters on the Moon, A&amp;A 699 L3.",
     "Abstract, §§2-4 lead. E06. Publisher abstract checked; full PDF download blocked.",
     "https://doi.org/10.1051/0004-6361/202555481","DOI"),
    (11,"LROC instrument-team factsheet; Robinson et al. instrument description.",
     "Factsheet p1; instrument description §3.1. E08. The ~5 km swath is a NAC-pair design value at 50 km altitude.",
     "https://www.lroc.asu.edu/assets/LROC_factsheet-1ea25e00953a1dc6e26774f2e6925bf5f4534712da4ce1c2dfc70f49c41acab6.pdf","Instrument factsheet"),
    (12,"Sony (2025), IMX636 flyer v1.0; Prophesee/Sony (2024), IMX636 product brief.",
     'Flyer p2; brief p1 and footnote. E15-E16. <link href="https://prophesee.ai/wp-content/uploads/2024/06/IMX636-AAMR-C-Product-Brief-2024-1.pdf" color="#245C88">Product brief</link>.',
     "https://www.sony-semicon.com/files/62/flyer_industry/IMX636-AAMR-Flyer.pdf","Manufacturer flyer"),
    (13,"Graca et al. (2024), SciDVS, arXiv:2409.09648v1.",
     "PDF pp1,3, Fig. 5. E17. The 1.7% contrast result is at 0.7 lx and 18 Hz bandwidth.",
     "https://arxiv.org/pdf/2409.09648v1","Author PDF"),
    (14,"Suggs, Ehlert and Moser (2017), Radiometric calibration techniques for lunar impact flashes, PSS 143, 225-229.",
     "Abstract and method preview. E19. Full paper not obtained.","https://doi.org/10.1016/j.pss.2017.04.016","DOI"),
    (15,"Scheerlinck, Barnes and Mahony (2018), Continuous-time Intensity Estimation Using Event Cameras, ACCV.",
     "Author v1 pp5-10 method; pp9-10 constructed benchmark; p12 Table 1. E27.",
     "https://arxiv.org/pdf/1811.00386v1","Author PDF"),
    (16,"Wang et al. (2024), An Asynchronous Linear Filter Architecture for Hybrid Event-Frame Cameras, TPAMI 46, 695-711.",
     "v2 abstract; v1 full HTML §§III-V, Appendix C. E32. Relative 69.4% absolute-intensity-error reduction is from v2 abstract; no v2 table claim.",
     "https://arxiv.org/abs/2309.01159","Versioned paper"),
    (17,"Madiedo et al. (2014), A large lunar impact blast on 2013 September 11, MNRAS 439, 2364-2369.",
     "Journal p2366 Fig. 4/Table 1; author v1 pp7-8,p23. E29. One exceptional event.",
     "https://doi.org/10.1093/mnras/stu083","DOI"),
    (18,"Yanagisawa et al. (2021), Low dispersion spectra of lunar impact flashes in 2018 Geminids, PSS 195, 105131.",
     "Publisher abstract/highlights/intro. E30. Full tables not obtained; spectral components are model interpretations.",
     "https://doi.org/10.1016/j.pss.2020.105131","DOI"),
    (19,"Bouley et al. (2012), Power and duration of impact flashes on the Moon, Icarus 218, 115-124.",
     "Publisher abstract/section previews. E31. Mixed historical instruments and selection criteria.",
     "https://doi.org/10.1016/j.icarus.2011.11.028","DOI"),
    (20,"Bonanos et al. (2018), NELIOTA: First temperature measurement of lunar impact flashes, A&amp;A 612 A76.",
     "Supplied PDF pp2-5, Table 1 and photometry equations. E02. Historical two-camera synchronization is stated as better than 6 ms.",
     "https://doi.org/10.1051/0004-6361/201732109","DOI"),
    (21,"Sheward et al. (2026), Twin Impact Lunar Telescope network: observations of the 2025 Geminids, MNRAS 551 stag1433.",
     "§§3.2,4.1-4.2; modelled energy in readout gaps. E22. Primary full HTML checked.",
     "https://doi.org/10.1093/mnras/stag1433","DOI"),
    (22,"Liakos et al. (2020), NELIOTA: Methods, statistics and results, A&amp;A 633 A112.",
     "Author v1 pp18-19 Tables 4-5; §§6.2-6.4,7. E33. The last KE column has units 10^7 J. Journal PDF access failed; version retained explicitly.",
     "https://arxiv.org/pdf/1911.06101v1","Author PDF"),
    (23,"Suggs et al. (2014), The flux of kilogram-sized meteoroids from lunar impact monitoring, Icarus 238,23-36.",
     "Supplied PDF Tables 1,3; §§4.3-4.5, Figs 7-11. E01. Peak-field R energy is not integrated NELIOTA R+I energy.",
     "https://doi.org/10.1016/j.icarus.2014.04.032","DOI"),
    (24,"Robinson et al. (2026), A new 222-m diameter lunar crater, Science Advances 12 eaeh7812.",
     "Primary PMC indexed full text: Introduction, Fig. 1, Tables 1-2, topographic method. E34. Published 16 September; direct PMC fetch challenged. Crater-derived KE, not a flash observation.",
     "https://doi.org/10.1126/sciadv.aeh7812","Primary paper"),
    (25,"Horányi et al. (2015), A permanent, asymmetric dust cloud around the Moon, Nature 522,324-326.",
     "Full author PDF pp1-3/Figs 1-3 and Methods. E35. Secondary ejecta, not measured primary impactor energies.",
     "https://spacephysics.princeton.edu/sites/g/files/toruqf1376/files/media/15_horanyi_a.pdf","Author PDF"),
    (26,"Moorhead (2020), NASA Meteoroid Engineering Model Version 3, NASA/TM-2020-220555.",
     'Guide §2/2.1 and Fig. 1; E36. Model range, not lunar flash data. <link href="https://arxiv.org/pdf/1909.05947v2" color="#245C88">Moorhead et al. author v2</link> pp17-18,23 compare spacecraft impacts and document limits.',
     "https://ntrs.nasa.gov/citations/20200000563","NASA guide"),
    (27,"Pokorný et al. (2019), Meteoroids at the Moon, JGR Planets 124,752-778.",
     "Full primary PDF abstract; §3/Figs 7-12; discussion. E37. Small-meteoroid model; its flux normalization is not transferred to gram-scale flashes.",
     "https://doi.org/10.1029/2018JE005912","DOI"),
    (28,"Liu et al. (2026), Meteoroid flux at sub-meter scales is homogeneous across the Lunar nearside and farside, CEE 7,289.",
     "Final PDF abstract; Results, size-frequency distribution; Methods/Fig. 2. E38. Published 20 February, version of record 30 March. Long-time/local sample inference.",
     "https://doi.org/10.1038/s43247-026-03270-z","Primary paper"),
    (29,"Rizos et al. (2026), From flash to crater, MNRAS 545 staf2068 (online 21 November 2025).",
     "Primary full HTML Introduction, §§3.1,4-5; E39. Optical record statement, 35±0.7 m crater and revised source association.",
     "https://doi.org/10.1093/mnras/staf2068","Primary paper"),
]
for n,title,locator,url,label in references:
    if n in (12,22):
        page()
        heading("Sources and verification trail (continued)")
    add(f'<b>[{n}] {title}</b> {locator} <link href="{escape(url, quote=True)}" color="#245C88">{label}</link>.', "ref")
heading("Reproduce or inspect the calculations", 2)
add("<b>Workbook:</b> outputs/d01_d04_research_2026-10-28/d01_d04_research.xlsx. "
    "The Photon budget and Localization sheets keep the reference calculations. The Light curves and Reconstruction sheets add "
    "source records, analytic examples and test targets. The Energy distribution and Energy catalogue sheets add 192 source rows and "
    "the population limits, and the Evidence and Decisions sheets keep the status and access limits.", "small")
add("<b>Analysis:</b> analysis/d01_d04_research/README.md gives the exact commands. The inputs are in model_inputs.json, and "
    "calculate.py produces model_results.json and the 54-row parameter_sweep.csv. The PDF is generated by build_report.py. "
    "calculate_lightcurves.py reads lightcurve_inputs.json and writes lightcurve_results.json; --figures prepares the cited excerpts. "
    "calculate_energy_distribution.py reads the source text cache and writes the CSV/JSON under data/lunar_impact_energy, "
    "energy_distribution_results.json and Figure C. Source tokens, pages and checksums allow an audit. "
    "The reference photon and geometry results agree with the saved workbook. No new calibrated sensor capability is claimed.", "small")


class ReviewDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, "outline_text"):
            self.outline_count = getattr(self, "outline_count", 0) + 1
            key = f"section-{self.outline_count}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.outline_text, key, level=0, closed=False)


TOTAL_PAGES = 0


def header(c, doc):
    c.saveState()
    c.setFillColor(MUTED)
    c.setFont("Arial", 7.7)
    c.drawString(LEFT, PAGE_H-25, "SPACE MISSION DESIGN")
    c.drawRightString(PAGE_W-RIGHT, PAGE_H-25, "Lunar impact flashes | 28 October 2026")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(LEFT, PAGE_H-33, PAGE_W-RIGHT, PAGE_H-33)
    c.line(LEFT, 33, PAGE_W-RIGHT, 33)
    c.setFont("Arial", 7.7)
    c.drawString(LEFT, 21, "D01-D04 | Internal working report | Proposed values")
    c.drawRightString(PAGE_W-RIGHT, 21, f"{doc.page} / {TOTAL_PAGES}" if TOTAL_PAGES else str(doc.page))
    c.restoreState()


def make_doc(target):
    return ReviewDoc(target, pagesize=A4, rightMargin=RIGHT, leftMargin=LEFT,
                topMargin=46, bottomMargin=45,
                title="Lunar impact-flash mission: D01-D04 research review",
                author="Space Mission Design", subject="Internal candidate values, evidence, assumptions and next steps")


# A normal canvas preserves PDF bookmark destinations. First pass is kept in memory.
first_pass = BytesIO()
make_doc(first_pass).build(deepcopy(story), onFirstPage=header, onLaterPages=header)
TOTAL_PAGES = len(PdfReader(BytesIO(first_pass.getvalue())).pages)
make_doc(str(OUT)).build(story, onFirstPage=header, onLaterPages=header)
reader = PdfReader(OUT)
report = {"pdf": str(OUT), "pages": len(reader.pages), "characters_per_page": [len(x.extract_text()) for x in reader.pages]}
qa = ROOT / "tmp" / "pdfs" / "d01_d04_report"
qa.mkdir(parents=True, exist_ok=True)
(qa / "text.txt").write_text("\n\n".join(f"=== PAGE {i+1} ===\n{x.extract_text()}" for i,x in enumerate(reader.pages)), encoding="utf-8")
(qa / "build_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
