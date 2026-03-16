import json
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import DictLoader, Environment

from web.embedded_assets import INDEX_TEMPLATE, RESULT_TEMPLATE, STYLE_CSS
from web.presenter import build_result_context
from web.service import analyze_paifu


BASE_DIR = Path(__file__).resolve().parent
FAVICON_PATH = BASE_DIR / "static" / "favicon.ico"
FALLBACK_FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
    "<rect width='64' height='64' rx='12' fill='#2f6feb'/>"
    "<text x='50%' y='53%' dominant-baseline='middle' text-anchor='middle' "
    "font-size='34' fill='white'>麻</text>"
    "</svg>"
)

app = FastAPI(title="雀魂 牌譜リザルト")
HAS_FILE_ASSETS = (BASE_DIR / "static").is_dir() and (BASE_DIR / "templates").is_dir()

if HAS_FILE_ASSETS:
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
else:
    templates = None
    embedded_env = Environment(
        loader=DictLoader(
            {
                "index.html": INDEX_TEMPLATE,
                "result.html": RESULT_TEMPLATE,
            }
        )
    )


def _render_template(request: Request, name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    context_with_request = dict(context)
    context_with_request["request"] = request
    if HAS_FILE_ASSETS:
        return templates.TemplateResponse(
            request=request,
            name=name,
            context=context_with_request,
            status_code=status_code,
        )
    template = embedded_env.get_template(name)
    return HTMLResponse(content=template.render(**context_with_request), status_code=status_code)


def _decode_upload(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "牌譜ファイルの文字コードを判定できませんでした。")


def _to_int(payload: dict, key: str, default: int) -> int:
    try:
        return int(payload.get(key, default))
    except Exception:
        return default


def _render_analyze_result(request: Request, paifu_json: dict, settings: dict) -> HTMLResponse:
    users = analyze_paifu(
        paifu_json=paifu_json,
        samma=False,
        rate=settings["rate"],
        chip=settings["chip"],
        uma_1=settings["uma_1"],
        uma_2=settings["uma_2"],
        oka_1=settings["oka_1"],
        oka_2=settings["oka_2"],
        all_star_chip=settings["all_star_chip"],
        yiman_tumo_chip=settings["yiman_tumo_chip"],
        yiman_chip=settings["yiman_chip"],
    )
    context = build_result_context(users)
    context["settings"] = settings
    return _render_template(
        request=request,
        name="result.html",
        context=context,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_template(request=request, name="index.html", context={"error": None})


@app.get("/favicon.ico")
async def favicon() -> Response:
    if FAVICON_PATH.is_file():
        return FileResponse(FAVICON_PATH, media_type="image/x-icon")
    return Response(content=FALLBACK_FAVICON_SVG, media_type="image/svg+xml; charset=utf-8")


if not HAS_FILE_ASSETS:

    @app.get("/static/style.css")
    async def static_style() -> Response:
        return Response(content=STYLE_CSS, media_type="text/css; charset=utf-8")


@app.post("/analyze-json", response_class=HTMLResponse)
async def analyze_json(
    request: Request,
    payload: dict = Body(...),
) -> HTMLResponse:
    try:
        paifu_json = payload["paifu_json"]
        settings = {
            "rate": _to_int(payload, "rate", 50),
            "chip": _to_int(payload, "chip", 500),
            "uma_1": _to_int(payload, "uma_1", 10),
            "uma_2": _to_int(payload, "uma_2", 20),
            "oka_1": _to_int(payload, "oka_1", 25000),
            "oka_2": _to_int(payload, "oka_2", 30000),
            "all_star_chip": _to_int(payload, "all_star_chip", 5),
            "yiman_tumo_chip": _to_int(payload, "yiman_tumo_chip", 5),
            "yiman_chip": _to_int(payload, "yiman_chip", 10),
        }
    except Exception as exc:
        return _render_template(
            request=request,
            name="index.html",
            context={"error": f"リクエストの解析に失敗しました: {exc}"},
            status_code=400,
        )

    try:
        return _render_analyze_result(request=request, paifu_json=paifu_json, settings=settings)
    except Exception as exc:
        return _render_template(
            request=request,
            name="index.html",
            context={"error": f"精算処理に失敗しました: {exc}"},
            status_code=400,
        )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    paifu_file: UploadFile = File(...),
    rate: int = Form(50),
    chip: int = Form(500),
    uma_1: int = Form(10),
    uma_2: int = Form(20),
    oka_1: int = Form(25000),
    oka_2: int = Form(30000),
    all_star_chip: int = Form(5),
    yiman_tumo_chip: int = Form(5),
    yiman_chip: int = Form(10),
) -> HTMLResponse:
    try:
        raw = await paifu_file.read()
        paifu_text = _decode_upload(raw)
        paifu_json = json.loads(paifu_text)
    except Exception as exc:
        return _render_template(
            request=request,
            name="index.html",
            context={"error": f"牌譜ファイルの読み込みに失敗しました: {exc}"},
            status_code=400,
        )

    settings = {
        "rate": rate,
        "chip": chip,
        "uma_1": uma_1,
        "uma_2": uma_2,
        "oka_1": oka_1,
        "oka_2": oka_2,
        "all_star_chip": all_star_chip,
        "yiman_tumo_chip": yiman_tumo_chip,
        "yiman_chip": yiman_chip,
    }

    try:
        return _render_analyze_result(request=request, paifu_json=paifu_json, settings=settings)
    except Exception as exc:
        return _render_template(
            request=request,
            name="index.html",
            context={"error": f"精算処理に失敗しました: {exc}"},
            status_code=400,
        )
