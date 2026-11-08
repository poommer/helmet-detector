from pathlib import Path
import shutil
import math
import yaml

ROOT = Path(__file__).resolve().parent

def main():
    source = ROOT / 'dataset'
    target = ROOT / 'dataset-detect'
    if target.exists():
        raise FileExistsError('dataset-detect already exists; no files overwritten.')
    config = yaml.safe_load((source / 'data.yaml').read_text(encoding='utf-8-sig'))
    converted = {}
    # Validate all labels before creating the derived dataset.
    for split in ('train', 'valid', 'test'):
        for label in (source / split / 'labels').glob('*.txt'):
            output = []
            for number, line in enumerate(label.read_text().splitlines(), 1):
                if not line.strip():
                    continue
                parts = line.split()
                idx = int(parts[0])
                coords = list(map(float, parts[1:]))
                if not 0 <= idx < len(config['names']) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in coords):
                    raise ValueError(f'Invalid annotation {label}:{number}')
                if len(coords) == 4:
                    output.append(line)
                elif len(coords) >= 6 and len(coords) % 2 == 0:
                    xs, ys = coords[::2], coords[1::2]
                    x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f'Degenerate polygon {label}:{number}')
                    output.append(f'{idx} {(x1+x2)/2:.10f} {(y1+y2)/2:.10f} {x2-x1:.10f} {y2-y1:.10f}')
                    converted[split] = converted.get(split, 0) + 1
                else:
                    raise ValueError(f'Unknown annotation format {label}:{number}')
            converted[label] = '\n'.join(output) + ('\n' if output else '')
    shutil.copytree(source, target)
    for label, content in converted.items():
        if isinstance(label, Path):
            (target / label.relative_to(source)).write_text(content, encoding='utf-8')
    config.pop('path', None)
    for key, split in [('train','train'),('val','valid'),('test','test')]:
        if key in config:
            config[key] = f'{split}/images'
    (target / 'data.yaml').write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding='utf-8')
    print('Derived dataset:', target)
    print('Polygons converted:', {k:v for k,v in converted.items() if isinstance(k,str)})
    print('Original dataset unchanged.')

if __name__ == '__main__':
    main()
