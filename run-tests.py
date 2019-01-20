import glob
import os


def main():
    report = {}
    files = glob.glob('tests/*.asm')
    for filename in files:
        base = os.path.splitext(filename)[0]
        print(f'{"-" * 32} Testing {base} {"-" * 32}')
        rc = os.system(f'python3 lc3.py {filename}')
        if rc:
            report[filename] = False
            continue
        with open(f'{base}.obj', 'rb') as f1:
            with open(f'{base}-out.obj', 'rb') as f2:
                report[filename] = f1.read() == f2.read()
        os.remove(f'{base}-out.obj')

    print('-' * 32, 'RESULSTS', '-' * 32)
    for filename, ok in report.items():
        print(f'{filename:<32} {"OK" if ok else "FAIL"}')


if __name__ == '__main__':
    main()
