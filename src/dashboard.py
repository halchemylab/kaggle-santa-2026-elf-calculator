"""Build an offline dashboard from saved benchmark reports; no dependencies."""

import argparse
import json
import os
from pathlib import Path


def build_dashboard(runs='runs', output=None):
    directory = Path(runs)
    destination = Path(output) if output else directory / 'dashboard.html'
    reports = []
    for path in sorted(directory.glob('*/report.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        if report.get('schema_version') != 1:
            raise ValueError(f'Unsupported benchmark report: {path}')
        report['artifact_prefix'] = os.path.relpath(path.parent, destination.parent).replace('\\', '/')
        reports.append(report)
    template = Path(__file__).with_name('dashboard.html').read_text(encoding='utf-8')
    # Escape script delimiters, including labels supplied on the command line.
    payload = json.dumps(reports, ensure_ascii=True).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(template.replace('__BENCHMARK_DATA__', payload), encoding='utf-8')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', default='runs')
    parser.add_argument('--output')
    args = parser.parse_args()
    print(build_dashboard(args.runs, args.output))
