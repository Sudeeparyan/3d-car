#!/usr/bin/env python3
"""One entry point for the 160 mm Mustang gift model.

Uses only the Python standard library, so it runs with any Python 3.8+ before the
virtual environment exists (creating the venv itself needs Python 3.11+, ideally 3.12). Every pipeline step is then executed with the project's
own .venv Python.  Run  python run.py --help  or see README.md ("Run it").

Commands
  setup            create .venv, install requirements.txt, npm install, check Chrome
  check            report what is installed / missing (Python, packages, Node, Chrome, inputs)
  view             serve the folder locally and open viewer.html / START_HERE.html
  build            full pipeline: body -> parts -> paint -> OBJ -> renders -> likeness ->
                   multicolour -> validate -> previews -> START_HERE.html + ZIP
  step <name>...   run one or more pipeline steps by name (python run.py step --list)
  plate <TEXT>     set the rear number plate text in scripts/geometry.py (then: build --skip-body)
  clean            delete regenerated work/ files (forces the slow body rebuild)
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import platform
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
WORK = ROOT / 'work'
LIKENESS = ROOT / 'validation/likeness'
SOURCE_STL = ROOT / 'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl'
MIN_PYTHON = (3, 11)   # the pinned numpy/scipy wheels need 3.11+; 3.12 is what the files were built with
RENDER_VIEWS = 'three,side,sideR,side_persp,front,rear,rear34,top,wheel,grille,frontlow,rearlow'
PROMOTED_FILES = ['likeness.json', 'contact_sheet.jpg', 'profile_compare.png', 'three.png', 'rear34.png', 'side.png',
                  'front.png', 'rear.png', 'top.png', 'wheel.png', 'grille.png', 'frontlow.png', 'rearlow.png', 'side_persp.png']
CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\Application\chrome.exe'),
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/snap/bin/chromium', '/usr/bin/microsoft-edge',
]


# ----------------------------------------------------------------------------- helpers
def say(msg: str) -> None:
    print(f'\n=== {msg}', flush=True)


def fail(msg: str, code: int = 1) -> None:
    print(f'ERROR: {msg}', file=sys.stderr, flush=True)
    sys.exit(code)


def venv_python() -> Path:
    return VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def find_chrome() -> str | None:
    env = os.environ.get('CHROME_PATH')
    if env and Path(env).exists():
        return env
    for candidate in CHROME_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_cmd(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str | Path], **kw) -> subprocess.CompletedProcess:
    """Run a command from the project root, echoing it, and stop on failure."""
    printable = ' '.join(str(c) for c in cmd)
    print(f'$ {printable}', flush=True)
    t0 = time.time()
    try:
        result = subprocess.run([str(c) for c in cmd], cwd=ROOT, check=True, **kw)
    except FileNotFoundError:
        fail(f'command not found: {cmd[0]}')
    except subprocess.CalledProcessError as e:
        fail(f'step failed (exit {e.returncode}): {printable}', e.returncode)
    print(f'  done in {time.time() - t0:.0f}s', flush=True)
    return result


def py(script: str, *args: str) -> None:
    exe = venv_python()
    if not exe.exists():
        fail(f'{exe} not found. Run:  python run.py setup')
    run([exe, ROOT / 'scripts' / script, *args])


def require_node() -> str:
    node = node_cmd('node')
    if not node:
        fail('Node.js is not installed (needed for the headless renders). Install Node 18+ from https://nodejs.org '
             'or skip renders with:  python run.py build --no-render')
    if not (ROOT / 'node_modules/puppeteer-core').exists():
        fail('node_modules missing. Run:  python run.py setup   (or: npm install)')
    if not find_chrome():
        fail('Google Chrome not found. Install it, or set CHROME_PATH to the browser executable, '
             'or skip renders with:  python run.py build --no-render')
    return node


# ----------------------------------------------------------------------------- setup / check
def cmd_setup(a: argparse.Namespace) -> None:
    say(f'1/3  Python virtual environment at {VENV.relative_to(ROOT)}')
    if not venv_python().exists():
        # The venv copies the interpreter that launched run.py, so that one must be new enough.
        if sys.version_info < MIN_PYTHON:
            fail(f'Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required to create the environment, but run.py was started '
                 f'with {platform.python_version()} ({sys.executable}).\n'
                 '       Install Python 3.12 from https://www.python.org/downloads/ and run e.g.  python3.12 run.py setup  '
                 '(Windows:  py -3.12 run.py setup)')
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV)
    run([venv_python(), '-m', 'pip', 'install', '--upgrade', 'pip'])
    run([venv_python(), '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt'])

    say('2/3  Node packages (three.js + puppeteer-core for the renders)')
    npm = node_cmd('npm')
    if npm:
        run([npm, 'install', '--no-audit', '--no-fund'])
    else:
        print('  npm not found - skipped. Install Node 18+ from https://nodejs.org if you want renders/previews.')

    say('3/3  Google Chrome (used headless by the renderer)')
    chrome = find_chrome()
    print(f'  {"found: " + chrome if chrome else "NOT found - install Chrome or set CHROME_PATH (renders will be skipped)"}')
    say('Setup complete. Next:  python run.py check   then   python run.py build')


def cmd_check(a: argparse.Namespace) -> int:
    problems = 0

    def row(ok: bool, label: str, detail: str = '') -> None:
        nonlocal problems
        problems += 0 if ok else 1
        print(f'  [{"ok" if ok else "MISSING"}] {label}{" - " + detail if detail else ""}')

    say('Environment check')
    print(f'  [info] run.py launched with Python {platform.python_version()} ({sys.executable})')
    vp = venv_python()
    if vp.exists():
        ver = subprocess.run([str(vp), '-c', 'import platform;print(platform.python_version())'], capture_output=True, text=True).stdout.strip()
        ok = tuple(int(x) for x in ver.split('.')[:2]) >= MIN_PYTHON if ver else False
        row(ok, f'virtual environment {vp.relative_to(ROOT)} - Python {ver or "?"}', '' if ok else f'needs {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+: delete .venv and re-run setup with a newer Python')
        probe = ('import numpy, scipy, trimesh, manifold3d, skimage, cv2, PIL, fast_simplification, rtree;'
                 'from importlib.metadata import version as v;'
                 'print("trimesh", v("trimesh"), "manifold3d", v("manifold3d"), "numpy", v("numpy"))')
        r = subprocess.run([str(vp), '-c', probe], capture_output=True, text=True)
        row(r.returncode == 0, 'Python packages from requirements.txt',
            r.stdout.strip() if r.returncode == 0 else r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'import failed')
    else:
        row(False, f'virtual environment {vp.relative_to(ROOT)}', 'run: python run.py setup')
    node = node_cmd('node')
    row(bool(node), 'Node.js', subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip() if node else 'optional: renders/previews only')
    row((ROOT / 'node_modules/puppeteer-core').exists(), 'node_modules (npm install)', '' if (ROOT / 'node_modules/puppeteer-core').exists() else 'optional: renders/previews only')
    chrome = find_chrome()
    row(bool(chrome), 'Google Chrome / Chromium / Edge', chrome or 'optional: set CHROME_PATH')

    say('Inputs')
    row(SOURCE_STL.exists(), 'source body STL', str(SOURCE_STL.relative_to(ROOT)))
    photos = sorted((ROOT / 'images').glob('*.jpg'))
    row(len(photos) >= 6, f'{len(photos)} reference photographs in images/')
    row((LIKENESS / 'photo3_mask.png').exists(), 'side-photo silhouette mask (validation/likeness/photo3_mask.png)')

    say('Generated state')
    body = WORK / 'body_clean.stl'
    print(f'  [{"ok" if body.exists() else "absent"}] work/body_clean.stl - {"body already built, --skip-body is allowed" if body.exists() else "first build will take several minutes (about 11 min on a 2020s laptop)"}')
    for rel in ['print/01_body_160mm.stl', 'multicolor/body_color_parts.3mf', 'model/Mustang_160mm_assembled.obj',
                'previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png', 'START_HERE.html', 'Mustang_Gift_Package.zip']:
        print(f'  [{"ok" if (ROOT / rel).exists() else "absent"}] {rel}')
    print(f'\n{"All required items present." if problems == 0 else f"{problems} item(s) missing - see above."}')
    return problems


# ----------------------------------------------------------------------------- pipeline steps
STEPS: dict[str, tuple[str, callable]] = {}


def step(name: str, doc: str):
    def deco(fn):
        STEPS[name] = (doc, fn)
        return fn
    return deco


@step('build_body', 'voxel-repair, smooth and simplify the source body -> work/body_clean.stl (3-12 min depending on the machine, cached)')
def step_build_body(a) -> None:
    py('build_body.py')


@step('build_parts', 'add grille, lamps, mirrors, spoiler, badges, wheels -> print/*.stl, work/manifest.json')
def step_build_parts(a) -> None:
    py('build_parts.py')


@step('paint', 'compute the colour regions per triangle -> work/*_painted.npz')
def step_paint(a) -> None:
    py('paint_mesh.py')


@step('assemble', 'write the coloured preview assembly -> model/Mustang_160mm_assembled.obj/.mtl')
def step_assemble(a) -> None:
    py('assemble_obj.py')


@step('render', 'headless three.js renders of the assembly -> validation/likeness/<name>/ (needs Node + Chrome)')
def step_render(a) -> None:
    node = require_node()
    out = LIKENESS / a.name
    out.mkdir(parents=True, exist_ok=True)
    run([node, ROOT / 'scripts/render_views.mjs', '--obj', 'model/Mustang_160mm_assembled.obj', '--out', out,
         '--views', RENDER_VIEWS, '--modes', 'shaded,flat,silhouette'])


@step('likeness', 'score the renders against the six photographs -> validation/likeness/<name>/likeness.json')
def step_likeness(a) -> None:
    py('validate_likeness.py', str(LIKENESS / a.name))


@step('promote', 'copy the scored run into validation/likeness/final (the tracked, packaged one)')
def step_promote(a) -> None:
    src = LIKENESS / a.name
    dst = LIKENESS / 'final'
    if not (src / 'likeness.json').exists():
        fail(f'{src.relative_to(ROOT)}/likeness.json not found - run the render and likeness steps first')
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for f in PROMOTED_FILES:
        shutil.copyfile(src / f, dst / f)
    print(f'promoted {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}')


@step('multicolor', 'split body and wheel into colour volumes -> multicolor/*.stl, *.3mf, validation.json')
def step_multicolor(a) -> None:
    py('build_multicolor.py')


@step('validate', 'mesh checks of the six print STLs -> validation/GEOMETRY_REPORT.md')
def step_validate(a) -> None:
    py('validate_parts.py')


@step('previews', 'the 18 preview images -> previews/ (needs Node + Chrome)')
def step_previews(a) -> None:
    require_node()
    py('make_previews.py')


@step('package', 'colour diagram, START_HERE.html, checksums and Mustang_Gift_Package.zip')
def step_package(a) -> None:
    py('package_handoff.py')


BUILD_ORDER = ['build_body', 'build_parts', 'paint', 'assemble', 'render', 'likeness', 'promote',
               'multicolor', 'validate', 'previews', 'package']
RENDER_STEPS = {'render', 'likeness', 'promote', 'previews'}


def cmd_build(a: argparse.Namespace) -> None:
    if not venv_python().exists():
        fail('.venv not found. Run:  python run.py setup')
    if not SOURCE_STL.exists():
        fail(f'source body missing: {SOURCE_STL.relative_to(ROOT)} - copy the whole reference_assets/ folder')
    steps = list(BUILD_ORDER)
    skip_body = a.skip_body and (WORK / 'body_clean.stl').exists()
    if a.skip_body and not skip_body:
        print('work/body_clean.stl is missing, so the body will be built despite --skip-body.')
    if skip_body:
        steps.remove('build_body')
    render_ok = bool(node_cmd('node') and (ROOT / 'node_modules/puppeteer-core').exists() and find_chrome())
    if a.no_render or not render_ok:
        if not a.no_render:
            print('Node/Chrome not available - skipping renders, likeness score and previews. '
                  'Existing previews/ and validation/likeness/final are reused by the package step.')
        steps = [s for s in steps if s not in RENDER_STEPS]
    t0 = time.time()
    for i, name in enumerate(steps, 1):
        say(f'{i}/{len(steps)}  {name}: {STEPS[name][0]}')
        STEPS[name][1](a)
    say(f'Build complete in {(time.time() - t0) / 60:.1f} min')
    print('  Print files ........ print/  and  multicolor/')
    print('  Preview + guide .... START_HERE.html, previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png, docs/PRINT_AND_PAINT_GUIDE.html')
    print('  Hand-off archive ... Mustang_Gift_Package.zip')
    lk = LIKENESS / 'final/likeness.json'
    if lk.exists():
        import json
        s = json.loads(lk.read_text())['summary']
        print(f'  Photo likeness ..... {s.get("score_percent", "?")} % ({s.get("features_passed", "?")}/{s.get("features_total", "?")} features)')


def cmd_step(a: argparse.Namespace) -> None:
    if a.list or not a.names:
        print('Pipeline steps in order (python run.py step <name> [<name>...]):')
        for n in BUILD_ORDER:
            print(f'  {n:12s} {STEPS[n][0]}')
        return
    for n in a.names:
        if n not in STEPS:
            fail(f'unknown step "{n}". Run:  python run.py step --list')
    for n in a.names:
        say(f'{n}: {STEPS[n][0]}')
        STEPS[n][1](a)


# ----------------------------------------------------------------------------- plate / clean / view
def cmd_plate(a: argparse.Namespace) -> None:
    geometry = ROOT / 'scripts/geometry.py'
    src = geometry.read_text(encoding='utf-8')
    pattern = re.compile(r"^PLATE_TEXT = (['\"]).*?\1", re.M)
    if not pattern.search(src):
        fail('PLATE_TEXT assignment not found in scripts/geometry.py')
    text = a.text.strip().upper()
    geometry.write_text(pattern.sub(f'PLATE_TEXT = {text!r}', src, count=1), encoding='utf-8')
    print(f'scripts/geometry.py: PLATE_TEXT = {text!r}')
    print('Now regenerate the files:  python run.py build --skip-body')


def cmd_clean(a: argparse.Namespace) -> None:
    if WORK.exists():
        shutil.rmtree(WORK)
        print('removed work/ - the next build rebuilds the body (several minutes)')
    else:
        print('work/ already absent')


def cmd_view(a: argparse.Namespace) -> None:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal readable
            pass

    handler = functools.partial(Quiet, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(('127.0.0.1', a.port), handler)
    except OSError as e:
        fail(f'cannot listen on port {a.port} ({e}). Try:  python run.py view --port 8001')
    page = 'START_HERE.html' if a.start else 'viewer.html'
    url = f'http://127.0.0.1:{a.port}/{page}'
    print(f'Serving {ROOT} at {url}   (Ctrl+C to stop)')
    if not a.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nstopped')


# ----------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog='python run.py', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='command', required=True)

    sub.add_parser('setup', help='create .venv, install requirements.txt and npm packages').set_defaults(fn=cmd_setup)
    sub.add_parser('check', help='report installed / missing tools and inputs').set_defaults(fn=lambda a: sys.exit(1 if cmd_check(a) else 0))

    v = sub.add_parser('view', help='serve the folder and open the 3D viewer in a browser')
    v.add_argument('--port', type=int, default=8000)
    v.add_argument('--start', action='store_true', help='open START_HERE.html instead of viewer.html')
    v.add_argument('--no-browser', action='store_true')
    v.set_defaults(fn=cmd_view)

    b = sub.add_parser('build', help='run the whole pipeline and produce the hand-off ZIP')
    b.add_argument('--name', default='current', help='likeness run folder under validation/likeness/ (default: current)')
    b.add_argument('--skip-body', action='store_true', help='reuse work/body_clean.stl instead of rebuilding the body')
    b.add_argument('--no-render', action='store_true', help='skip renders, likeness score and previews (no Node/Chrome needed)')
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser('step', help='run individual pipeline steps')
    s.add_argument('names', nargs='*')
    s.add_argument('--list', action='store_true')
    s.add_argument('--name', default='current', help='likeness run folder for render/likeness/promote')
    s.set_defaults(fn=cmd_step)

    p = sub.add_parser('plate', help='set the rear number-plate text (PLATE_TEXT in scripts/geometry.py)')
    p.add_argument('text')
    p.set_defaults(fn=cmd_plate)

    sub.add_parser('clean', help='delete work/ so the next build starts from the source body').set_defaults(fn=cmd_clean)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == '__main__':
    main()
