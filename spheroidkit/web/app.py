"""
Web API (FastAPI): a thin HTTP layer over the validated engine.

Endpoints:
  GET  /            -> serves the front-end
  GET  /health      -> liveness check (for uptime monitoring)
  POST /analyze     -> single image -> metrics (+ optional viability) + overlay
  POST /dose        -> concentrations + responses -> IC50 fit

The web layer adds NO science: it only marshals inputs to the engine and
serialises results. All computation lives in spheroidkit.* (engine-first).
"""
import io
import base64
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from ..config import Config, DEFAULT
from ..config import CalibrationConfig
from ..core.preprocess import preprocess
from ..core.segment import segment
from ..core.measure import measure_mask
from ..analysis.viability import viability_proxy
from ..analysis.doseresponse import fit_dose_response, curve_points

app = FastAPI(title="spheroidkit", version="0.6.0")

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_HERE, "static")


def _decode_image(raw: bytes) -> np.ndarray:
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "could not decode image")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _overlay_png(rgb, mask) -> str:
    """Draw the boundary on the image, return base64 PNG for the browser."""
    from skimage import measure as skmeasure
    vis = rgb.copy()
    for c in skmeasure.find_contours(mask.astype(float), 0.5):
        pts = np.fliplr(c).astype(np.int32)
        cv2.polylines(vis, [pts], False, (0, 255, 255), 6)
    ok, buf = cv2.imencode(".png", cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buf).decode()


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    um_per_px: float | None = Form(None),
    with_viability: bool = Form(False),
):
    rgb = _decode_image(await file.read())
    cfg = Config(calibration=CalibrationConfig(um_per_px=um_per_px)) \
        if um_per_px else DEFAULT
    flat = preprocess(rgb, cfg.preprocess)
    mask = segment(flat, cfg.segment)
    metrics = measure_mask(mask, cfg.calibration)
    out = {"metrics": metrics.as_dict(),
           "overlay_png_base64": _overlay_png(rgb, mask)}
    if with_viability:
        out["viability"] = viability_proxy(flat, mask, metrics.circularity).as_dict()
    return JSONResponse(out)


@app.post("/dose")
async def dose(
    concentrations: str = Form(...),   # comma-separated
    responses: str = Form(...),        # comma-separated % of control
    units: str = Form("uM"),
):
    try:
        conc = [float(x) for x in concentrations.split(",") if x.strip()]
        resp = [float(x) for x in responses.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(400, "concentrations/responses must be numeric")
    if len(conc) != len(resp) or len(conc) < 4:
        raise HTTPException(400, "need >=4 matching concentration/response pairs")
    fit = fit_dose_response(conc, resp, units=units)
    xs, ys = curve_points(fit)
    return JSONResponse({"fit": fit.as_dict(),
                         "curve": {"x": xs.tolist(), "y": ys.tolist()},
                         "points": {"x": conc, "y": resp}})


@app.get("/", response_class=HTMLResponse)
def index():
    idx = os.path.join(_STATIC, "index.html")
    if os.path.isfile(idx):
        with open(idx) as f:
            return f.read()
    return "<h1>spheroidkit</h1><p>front-end not found</p>"


if os.path.isdir(_STATIC):
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")
