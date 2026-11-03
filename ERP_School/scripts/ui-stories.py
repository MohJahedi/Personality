"""Create visibly synthetic UI stories in ignored build output, never an auth bypass."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--synthetic-api', action='store_true', required=True)
parser.add_argument('--view', choices=['home', 'settings', 'years', 'users', 'schedule', 'students', 'finance'], default='settings')
parser.add_argument('--size', choices=['small', 'normal', 'large'], default='normal')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
assets = root / 'web/assets'
script = next(assets.glob('index-*.js')).name
style = next(assets.glob('index-*.css')).name
(assets / 'qa-fixture.js').write_text((root / 'tests/ui/fixture.js').read_text())
(assets / 'qa-app.html').write_text(f'''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/assets/{style}"><title>آزمون رابط ساختگی ERP_School</title></head><body><div style="background:#fff3cd;color:#663c00;padding:5px;text-align:center;font:12px Tahoma">آزمون رابط · API و داده کاملاً ساختگی · محصول نهایی نیست</div><div id="root"></div><script src="/assets/qa-fixture.js"></script><script type="module" src="/assets/{script}"></script></body></html>''')
frames = ''.join(f'<iframe id="{name}" title="{name}" width="{width}" height="{height}" src="/assets/qa-app.html?size={args.size}#{args.view}"></iframe>' for name, width, height in [('small', 320, 850), ('phone', 390, 844), ('tablet', 820, 1180), ('desktop', 1440, 1000)])
(assets / 'qa.html').write_text('<!doctype html><html><meta charset="utf-8"><style>body{margin:0;background:#e2e8f0}iframe{display:block;border:0;margin:0 0 24px}</style>' + frames + '</html>')
print('Synthetic UI stories created. A normal build removes them.')
