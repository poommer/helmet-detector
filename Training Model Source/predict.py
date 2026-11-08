import argparse
from pathlib import Path
from check_gpu import check

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', required=True)
    parser.add_argument('--source', required=True, help='Image, video, folder, or 0 for webcam')
    parser.add_argument('--conf', type=float, default=0.25)
    args = parser.parse_args()
    check()
    from ultralytics import YOLO
    source = int(args.source) if args.source.isdecimal() else args.source
    for _ in YOLO(args.weights).predict(source=source, conf=args.conf, device=0,
            save=True, stream=True, project=str(Path(__file__).resolve().parent / 'runs'), name='predict'):
        pass

if __name__ == '__main__':
    main()
