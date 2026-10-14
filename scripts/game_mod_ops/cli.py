"""Structured CLI used by a chat executor or an existing Hub host. No resident API."""
from __future__ import annotations
import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from . import __version__
from .archive import inspect_zip
from .network import Budget
from .recipes import load_recipe, plan
from .safety import ModError, require
from .workflow import Job, default_data, acquire, import_archive, stage, nexus_files
from .umm import inventory, install_new, audit_installed, rollback_new

DEFAULT_RECIPE = Path(__file__).resolve().parents[2] / 'examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json'


def parser():
    p = argparse.ArgumentParser(description='Game Tool Hub mod workflows: explicit, bounded operations; no background service.')
    p.add_argument('--version', action='version', version=__version__)
    sub = p.add_subparsers(dest='action', required=True)
    for name in ('plan', 'catalog', 'nexus-files'):
        q = sub.add_parser(name)
        q.add_argument('--recipe', type=Path, default=DEFAULT_RECIPE)
        if name == 'plan':
            q.add_argument('--mode', default='real-time')
            q.add_argument('--select', nargs='+')
            q.add_argument('--file-pin', action='append', default=[], help='Exact Nexus item=file_id; obtain metadata with nexus-files first.')
            q.add_argument('--create-job', action='store_true', help='Save a new immutable local job; does not download.')
            q.add_argument('--data-dir', type=Path, default=default_data())
        if name == 'nexus-files':
            q.add_argument('--item', required=True); q.add_argument('--ask-nexus-key', action='store_true')
    for name in ('status', 'acquire', 'import-archive', 'stage', 'install-new', 'audit', 'rollback-new'):
        q = sub.add_parser(name)
        q.add_argument('--job', type=Path, required=True)
        if name not in ('status', 'acquire'): q.add_argument('--item', required=True)
        if name == 'acquire':
            q.add_argument('--allow-network', action='store_true')
            q.add_argument('--ask-nexus-key', action='store_true')
            q.add_argument('--max-mib', type=int, default=128)
            q.add_argument('--max-requests', type=int, default=40)
            q.add_argument('--seconds', type=int, default=300)
            q.add_argument('--nxm-item', help='Prompt locally for one fresh NXM link; the link is not a command-line argument or saved.')
        if name == 'import-archive':
            q.add_argument('--archive', type=Path, required=True)
            q.add_argument('--confirm-official-source', action='store_true')
        if name in ('install-new', 'rollback-new'):
            q.add_argument('--approve-plan', required=True, help='Full plan SHA-256 reviewed for this explicit operation.')
        if name == 'install-new':
            q.add_argument('--game-dir', type=Path, required=True)
            q.add_argument('--user-data-dir', type=Path, required=True, help='Kingmaker LocalLow user folder containing Saves; copied privately before deployment.')
            q.add_argument('--game-version', required=True, help='Game patch verified by the operator, not a guessed executable version.')
            q.add_argument('--umm-version', required=True)
            q.add_argument('--reviewed-umm-id')
    q = sub.add_parser('inspect-game'); q.add_argument('--game-dir', type=Path, required=True)
    q = sub.add_parser('inspect-archive'); q.add_argument('--archive', type=Path, required=True)
    q.add_argument('--expected-umm-id'); q.add_argument('--manager', action='store_true'); q.add_argument('--generic', action='store_true')
    return p


def local_key(ask=False):
    if ask:
        require(sys.stdin.isatty(), 'LOCAL_INPUT_REQUIRED', 'Enter the Nexus key only in a private local interactive terminal; do not send it to chat.')
        return getpass.getpass('Personal Nexus API key (hidden, not saved): ')
    return os.environ.get('NEXUS_MODS_API_KEY')


def dispatch(a):
    if a.action in ('plan', 'catalog', 'nexus-files'):
        r = load_recipe(a.recipe)
        if a.action == 'catalog': return r
        if a.action == 'nexus-files':
            matches = [i for i in r['items'] if i['id'] == a.item]
            require(len(matches) == 1, 'UNKNOWN_ITEM', 'Unknown recipe item.')
            return nexus_files(matches[0], local_key(a.ask_nexus_key))
        pins = {}
        for value in a.file_pin:
            name, separator, pin = value.partition('=')
            require(bool(separator) and pin.isdigit() and name not in pins, 'FILE_PIN_REQUIRED', 'Use each item=positive_file_id once.')
            pins[name] = int(pin)
        result = plan(r, a.select, a.mode, pins)
        if a.create_job:
            j = Job.create(a.data_dir, result)
            return {'job_private': str(j.path), **j.summary(), 'warnings': result['warnings']}
        return result
    if a.action == 'inspect-game': return inventory(a.game_dir)
    if a.action == 'inspect-archive': return inspect_zip(a.archive, a.expected_umm_id, a.manager, "generic" if a.generic else "umm")
    j = Job(a.job)
    if a.action == 'status': return j.summary()
    if a.action == 'acquire':
        require(a.allow_network, 'NETWORK_NOT_AUTHORIZED', 'Use allow-network for an explicit download action.')
        require(0 < a.max_mib <= 1024 and 0 < a.max_requests <= 100 and 0 < a.seconds <= 1800,
                'BUDGET_INVALID', 'Budgets must stay within 1 GiB, 100 requests and 30 minutes.')
        nxm = None
        if a.nxm_item:
            j.item(a.nxm_item)
            require(sys.stdin.isatty(), 'LOCAL_INPUT_REQUIRED', 'Enter NXM authorization only through a private local interactive terminal, or use manual import.')
            nxm = {a.nxm_item: getpass.getpass('Fresh Nexus NXM link (hidden, not saved): ')}
        return acquire(j, allow_network=a.allow_network, budget=Budget(a.max_mib*1024*1024, a.max_requests, a.seconds),
                       nexus_key=local_key(a.ask_nexus_key), nxm=nxm)
    if a.action == 'import-archive': return import_archive(j, a.item, a.archive, confirmed_source=a.confirm_official_source)
    if a.action == 'stage': return stage(j, a.item)
    if a.action == 'install-new':
        return install_new(j, a.item, a.game_dir, a.user_data_dir, approved_plan_sha256=a.approve_plan,
                           game_version=a.game_version, umm_version=a.umm_version, reviewed_umm_id=a.reviewed_umm_id)
    if a.action == 'audit': return audit_installed(j, a.item)
    if a.action == 'rollback-new': return rollback_new(j, a.item, a.approve_plan)
    raise ModError('UNSUPPORTED', 'Unsupported action.')


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        result = dispatch(a)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        # Batch output may contain waits/errors; it is not a blanket success.
        return 0 if not isinstance(result, dict) or all(i.get('status') in {'ACQUIRED','STAGED_NOT_INSTALLED','FILES_INSTALLED_RUNTIME_UNVERIFIED'} for i in result.get('items', [])) or a.action in {'plan','catalog','status'} else 2
    except ModError as e:
        print(json.dumps(e.record(), ensure_ascii=False)); return 2
    except KeyboardInterrupt:
        print(json.dumps({'status': 'INTERRUPTED_REVIEW_REQUIRED', 'message': 'Inspect this same job and its existing effects before resubmitting.'})); return 130
    except Exception:
        # Never dump tracebacks containing signed download links, keys or private paths.
        print(json.dumps({'status': 'UNEXPECTED_FAILURE', 'message': 'Operation stopped. Inspect the same job before retrying; no error URL or credential was logged.'})); return 3
