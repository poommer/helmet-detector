import argparse
from pathlib import Path
import yaml
from check_gpu import check

ROOT = Path(__file__).resolve().parent

def validate_in_fp32(validator):
    # This Ultralytics build uses FP16 validation even for BF16 training.
    # YOLO11x overflows on this ROCm/Windows build in FP16, so validate in FP32.
    if validator.training:
        validator.args.quantize = None

def prepare_dataset(source):
    source = Path(source).resolve()
    if not source.is_file() and source == (ROOT / 'dataset-detect' / 'data.yaml').resolve():
        original = ROOT / 'dataset' / 'data.yaml'
        if original.is_file() and not source.parent.exists():
            print('dataset-detect missing; preparing detection labels from dataset automatically.')
            from prepare_detect import main as prepare_detect
            prepare_detect()
    if not source.is_file():
        raise FileNotFoundError(f'Dataset missing: {source}. Put the Roboflow export in dataset/ or run prepare_detect.py. Existing dataset-detect folders are never overwritten automatically.')
    data = yaml.safe_load(source.read_text(encoding='utf-8-sig'))
    names = data.get('names')
    if not isinstance(names, (list, dict)) or not names:
        raise ValueError('data.yaml must define class names.')
    if isinstance(names, dict) and set(names) != set(range(len(names))):
        raise ValueError('Class IDs must be consecutive integers starting at 0.')
    print('Dataset classes:', names)
    # Preserve exported class IDs. Never invent new classes or relabel data.
    normalized = {'names': names, 'nc': len(names)}
    declared = Path(data.get('path') or '.')
    base = declared if declared.is_absolute() else source.parent / declared
    for split in ('train', 'val', 'test'):
        value = data.get(split)
        if not value:
            if split != 'test':
                raise ValueError(f'Missing {split} split')
            continue
        if not isinstance(value, str):
            raise ValueError('This starter supports directory-based YOLO exports, not lists of paths.')
        entry = Path(value)
        candidates = [entry] if entry.is_absolute() else [base / entry, source.parent / entry]
        # Some Roboflow exports use ../train/images with data.yaml at archive root.
        if not entry.is_absolute() and entry.parts and entry.parts[0] == '..':
            candidates.append(source.parent.joinpath(*entry.parts[1:]))
        resolved = next((p.resolve() for p in candidates if p.is_dir()), None)
        if resolved is None:
            raise FileNotFoundError(f'{split} images directory missing: {value}')
        images = [p for p in resolved.rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'}]
        labels = resolved.parent / 'labels'
        if not images or not labels.is_dir() or not any(labels.rglob('*.txt')):
            raise ValueError(f'{split} needs images and YOLO labels in sibling directories.')
        print(f'{split}: {len(images)} images; {labels}')
        normalized[split] = resolved.as_posix()
    output = ROOT / 'runs' / 'dataset-local.yaml'
    output.parent.mkdir(exist_ok=True)
    output.write_text(yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False), encoding='utf-8')
    return str(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=str(ROOT / 'dataset' / 'data.yaml'))
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch', type=int, default=4)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--model', default='yolo11n.pt')
    parser.add_argument('--workers', type=int, default=0)
    parser.add_argument('--cache', choices=['false', 'ram', 'disk'], default='false')
    parser.add_argument('--amp', action='store_true')
    parser.add_argument('--precision', choices=['fp32', 'fp16', 'bf16'], default=None)
    parser.add_argument('--nondeterministic', action='store_true')
    parser.add_argument('--name', default='helmet-yolo11')
    parser.add_argument('--optimizer', default='auto')
    parser.add_argument('--lr0', type=float, default=0.01)
    parser.add_argument('--check-data', action='store_true')
    args = parser.parse_args()
    data = prepare_dataset(args.data)
    if args.check_data:
        return
    check()
    from ultralytics import YOLO
    model = YOLO(args.model)
    if args.precision == 'bf16':
        model.add_callback('on_val_start', validate_in_fp32)
    model.train(data=data, epochs=args.epochs, batch=args.batch, imgsz=args.imgsz,
                device=0, workers=args.workers,
                amp=(False if args.precision == 'fp32' else args.precision) if args.precision else args.amp,
                cache=False if args.cache == 'false' else args.cache, hsv_h=0.0, hsv_s=0.0,
                hsv_v=0.15, project=str(ROOT / 'runs'), name=args.name, exist_ok=False,
                patience=20, seed=42, deterministic=not args.nondeterministic,
                optimizer=args.optimizer, lr0=args.lr0,
                warmup_bias_lr=0.0 if args.optimizer.lower() == 'adamw' else 0.1)

if __name__ == '__main__':
    main()
