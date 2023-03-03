import pathlib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-o', type=str, nargs=1)


def main():
    args = parser.parse_args()

    v = pathlib.Path('../../hardware')
    c = pathlib.Path('../c')
    tb = pathlib.Path('./tb.sv')

    print(tb.resolve().as_posix())
    with open(args.o[0], 'w') as outf:
        # Add tb and include lib 
        outf.write(tb.resolve().as_posix() + '\n')
        outf.write('+incdir+' + v.resolve().as_posix() + '\n\n')

        # Add all v files
        outf.writelines('\n'.join([p.resolve().as_posix() for p in v.glob('*.v')]) + '\n\n')

        # Add all c files
        outf.writelines('\n'.join([p.resolve().as_posix() for p in c.glob('*.c')]))

if __name__ == "__main__":
    main()