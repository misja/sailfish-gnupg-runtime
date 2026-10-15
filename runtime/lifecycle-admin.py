#!/usr/bin/python3 -I
"""Explicit owner-only administration; no package transaction or force/reset."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lifecycle_admission import Admission, AdmissionError
from lifecycle_control import Controller, Payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('initialize', 'close', 'recover', 'status'))
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args()
    admission = Admission('/var/lib/sailfish-gnupg-runtime')
    controller = Controller(admission, Payload())
    try:
        controller._owner()
        if args.action == 'initialize':
            result = {'state': 'ACTIVE', 'generation': controller.initialize()}
        elif args.action == 'close':
            result = {'state': controller.close(args.timeout), 'agents_registered': admission.agents_registered()}
        elif args.action == 'recover':
            result = {'state': 'ACTIVE', 'generation': controller.recover()}
        else:
            result = admission.status()
            controller.payload.verify(result['generation'])
            result['payload_matches'] = True
            result['agents_registered'] = admission.agents_registered()
        print(json.dumps(result, sort_keys=True))
        return 0
    except BlockingIOError:
        print('Lifecycle bootstrap, operation or agent registration is busy', file=sys.stderr)
        return 75
    except (AdmissionError, OSError, ValueError):
        print('Lifecycle trust or quiescence check failed; admission was not reopened', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
