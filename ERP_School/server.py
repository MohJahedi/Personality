"""Local development entry point and the v0.3 contract compatibility surface."""
import argparse
from pathlib import Path
import sys
import tempfile
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from socketserver import ThreadingMixIn

sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
from erp_school.bootstrap import create_application
from erp_school.core.values import money, day
from erp_school.modules.identity.passwords import password_matches, digest

School = create_application
__all__ = ['School', 'money', 'day', 'password_matches', 'digest']

class ThreadingServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass

def main():
    parser = argparse.ArgumentParser(description='ERP_School modular development server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data-dir', default=str(Path(__file__).resolve().parent / 'data'))
    parser.add_argument('--allow-host', action='append', default=[])
    parser.add_argument('--demo-data', action='store_true', help='Seed synthetic pilot data on first setup only.')
    parser.add_argument('--preview', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--strictPort', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.preview:
        args.data_dir = tempfile.mkdtemp(prefix='erp-school-foundation-v04-ui-qa-')
        args.allow_host.extend(['terminal.local', f'terminal.local:{args.port}'])
    application = create_application(args.data_dir,
        [f'localhost:{args.port}', f'127.0.0.1:{args.port}', *args.allow_host],
        seed_demo=args.demo_data)
    with make_server(args.host, args.port, application,
                     server_class=ThreadingServer, handler_class=QuietHandler) as server:
        print(f'ERP_School development: http://127.0.0.1:{args.port}/', flush=True)
        server.serve_forever()

if __name__ == '__main__':
    main()
