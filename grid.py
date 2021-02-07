#!/usr/local/bin/python3

import argparse
from math import ceil, floor

parser = argparse.ArgumentParser(description='calculate a grid.')

#./grid.py -nx 4 -ny 3 -element 51 -margin 10
#./grid.py -nx 3 -ny 2 -element 70 -margin 18

parser.add_argument('-x', type=float, default=320)
parser.add_argument('-y', type=float, default=180)
parser.add_argument('-nx', type=int, default=4)
parser.add_argument('-ny', type=int, default=3)

parser.add_argument('-fix', choices=['x', 'y'], default='y', help='-margin and -element fix the lengths along this axis')
parser.add_argument('-margin', type=float, default=10)

parser.add_argument('-element', type=float, default=51)
parser.add_argument('-ratio', type=float, default=4/3, help='x/y ratio')

args = parser.parse_args()
fixedlength = vars(args)[args.fix]
nfixed = vars(args)['n' + args.fix]
fixedremainder = fixedlength - 2 * args.margin - nfixed * args.element
fixedgap = fixedremainder / (nfixed - 1)

# multiply with this to get from fixed size to other size
ratio = args.ratio if args.fix == 'y' else 1 / args.ratio
freeelement = args.element * ratio
freegap = fixedgap * ratio

free = 'y' if args.fix == 'x' else 'x'
freelength = vars(args)[free]
nfree = vars(args)['n' + free]

freeremainder = freelength - (nfree - 1) * freegap - nfree * freeelement

print(f'layout for {args.nx}x{args.ny} {args.ratio} elements on a {args.x}x{args.y} page:')
print(f'  element size: {args.element} x {freeelement}')
print(f'  gap size:     {fixedgap} x {freegap}')
print(f'  margin:       {args.margin} x {freeremainder / 2} (on each side)')
