import json
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import DictLoader, Environment

from web.embedded_assets import INDEX_TEMPLATE, RESULT_TEMPLATE, STYLE_CSS
from web.presenter import build_result_context
from web.service import analyze_paifu


BASE_DIR = Path(__file__).resolve().parent

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_template(request=request, name="index.html", context={"error": None})


if not HAS_FILE_ASSETS:

    @app.get("/static/style.css")
    async def static_style() -> Response:
        return Response(content=STYLE_CSS, media_type="text/css; charset=utf-8")


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

    try:
        users = analyze_paifu(
            paifu_json=paifu_json,
            samma=False,
            rate=rate,
            chip=chip,
            uma_1=uma_1,
            uma_2=uma_2,
            oka_1=oka_1,
            oka_2=oka_2,
            all_star_chip=all_star_chip,
            yiman_tumo_chip=yiman_tumo_chip,
            yiman_chip=yiman_chip,
        )
    except Exception as exc:
        return _render_template(
            request=request,
            name="index.html",
            context={"error": f"精算処理に失敗しました: {exc}"},
            status_code=400,
        )

    context = build_result_context(users)
    context["settings"] = {
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
    return _render_template(
        request=request,
        name="result.html",
        context=context,
    )
