import pathlib
import argparse
import itertools

parser = argparse.ArgumentParser()
parser.add_argument('-v', type=str, nargs=1)
parser.add_argument('-c', type=str, nargs=1)


def main():
    args = parser.parse_args()

    v = pathlib.Path('../../hardware')
    c = pathlib.Path('../c')
    tb = pathlib.Path('./tb.sv')

    
    with open(args.v[0], 'w') as outf:
        # Add tb and include lib 
        outf.write(tb.resolve().as_posix() + '\n')
        outf.write('+incdir+' + v.resolve().as_posix() + '\n\n')

        # Add all v files
        outf.writelines('\n'.join([p.resolve().as_posix() for p in itertools.chain(v.glob('*.v'), v.glob('*.sv'))]) + '\n\n')
    print(f'Written {args.v[0]}')

    with open(args.c[0], 'w') as outf:
        # Add tb and include lib for header file gen
        outf.write(tb.resolve().as_posix() + '\n')
        outf.write('+incdir+' + v.resolve().as_posix() + '\n\n')

        # Add all c files minus the test file
        outf.writelines('\n'.join([p.resolve().as_posix() for p in c.glob('*.c') if p.name != 'test.c']))
    print(f'Written {args.c[0]}')

if __name__ == "__main__":
    main()