#!/usr/local/bin/python3.6

import argparse
import papersize
import os

from math import ceil, floor

parser = argparse.ArgumentParser(description='generate boxes of similar colors')

parser.add_argument('-paper', default='180mmx257mm', help='paper size (named size or couple)')
parser.add_argument('-landscape', default=False, action='store_true')
parser.add_argument('-margin', default='5mmx9mm', help='non-printable margin (length couple)')
parser.add_argument('-binding', default='9mm', help='binding margin')
parser.add_argument('-dots', default=.5, help='grayscale intensity of the dot grid from 0 (black) to 1 (white)')
parser.add_argument('-grid', default='5mm', help='grid distance')

#parser.add_argument('-fromtop', action='store_true', help='place first grid element starting at the top (default is bottom)')
#parser.add_argument('-fromright', action='store_true', help='place first grid element starting on the right (default is left)')

parser.add_argument('-gray', type=float, default=.2, help='grayscale intensity of text and lines, from 0 (black) to 1 (white)')
parser.add_argument('-gridgray', type=float, default=.5, help='grayscale intensity of the dot grid from 0 (black) to 1 (white)')
parser.add_argument('-line', '-lw', default='.5pt', help='line stroke width (any named size)')

parser.add_argument('-daily', type=int, default=8, help='add daily page, starting the schedule at the given hour')
parser.add_argument('-weekly', action='store_true', help='add daily page, starting the schedule at the given hour')

parser.add_argument('-gsdevice', default='pdfwrite', help='one of pdfwrite, eps2write etc, see https://www.ghostscript.com/doc/current/Devices.htm#High-level')
parser.add_argument('outfile', default='journal.pdf', help='the file to write the test page to')

args = parser.parse_args()

def mmtopt(mm):
  return mm * 2.835

def getpt(length):
  return mmtopt(float(papersize.parse_length(length, 'mm')))

def getpts(couple):
  return [ mmtopt(float(s)) for s in papersize.parse_couple(couple, 'mm') ]

try:
  size = getpts(args.paper)
  isnamedsize = False
except:
  size = papersize.parse_papersize(args.paper)
  isnamedsize = True

#if args.landscape:
#  size = papersize.rotate(size, papersize.LANDSCAPE)

# papersize is weird about pts
#size = [ papersize.convert_length(s, 'mm', 'pt') for s in size ]
#size = [ round(float(s) * 2.835) for s in size ]
args.line = getpt(args.line)
args.grid = getpt(args.grid)

args.margin = getpts(args.margin)
args.binding = getpt(args.binding)

gsfile = 'tmp.ps'
with open(gsfile, 'w') as f:

  def getx(x):
    return args.margin[0] + x * args.grid
  def gety(y):
    return size[1] - ( args.margin[1] + y * args.grid )

  postscript = []

  # extra such as setdash
  d = args.grid / 4 # 2
  def line(x, y, w = 0, h = 0, dash = False):
    # simple: http://paulbourke.net/dataformats/postscript/
    # full: https://www.adobe.com/content/dam/acom/en/devnet/actionscript/articles/psrefman.pdf
    r = f' newpath {getx(x)} {gety(y)} moveto {getx(x+w)} {gety(y+h)} lineto {f"[{d}] {d/2} setdash" if dash else "[ ] 0 setdash"} {args.line/2 if dash else args.line} setlinewidth {args.gray} setgray stroke '
    f.write(r)
    return r

  hd = .22 # half diameter -- first print was .225
  def box(x, y, s = 1):
    r = [ line(x + .5 - s*hd, y + .5 - s*hd, w=2*s*hd), line(x + .5 - s*hd, y + .5 - s*hd, h=2*s*hd), line(x + .5 + s*hd, y + .5 - s*hd, h=2*s*hd), line(x + .5 - s*hd, y + .5 + s*hd, w=2*s*hd) ]
    for s in r:
      f.write(s)
    return r

#  def grid(x, y, dx, dy, offsets = []):
#    return None # TODO

  def hook(x, y, w): # a bottom right hook/box -- the y is one less to correspond to text
    r = [ line(x+w, y-1, h=1), line(x, y, w=w) ]
    for s in r:
      f.write(s)
    return r

  lastsize = None
  # x, y interpreted as the cell/row AFTER that line
  def text(x, y, txt, size = 8, center = False, rotate = 0, todo = False):
    global lastsize
    # https://stackoverflow.com/questions/27383154/how-do-i-get-ghostscript-to-load-ttf-fonts-globally
    ps = '' if size == lastsize else f'/Helvetica findfont {size} scalefont setfont '
    lastsize = size
    # TODO implement todo
    ps = ps + f'{getx(x) + (.2 if center else 5)} {gety(y) + 1.1*size/2} moveto ({txt}) '
    if center:
      ps = ps + 'dup stringwidth pop 2 div neg 0 rmoveto'
    if rotate != 0:
      ps = ps + f' gsave {rotate} rotate show grestore '
    else:
      ps = ps + ' show '
    f.write(ps)
    return ps

  # always centered (on both axes)
  def mtext(x, y, txt, size = 7.5, center = True):
    txts = txt.split('\n')
  #  len(txts)
    # always deduct .5 to move from cell (text() interpretation of y) to actual line
    # 1: 0
    # 2: +-e/2
    # 3: +e, 0, -e
    totaldist = (len(txts) - 1) * (size - 1) / 10
    # +.1 to shift everything slighty above center
    offsets = [ .05 + totaldist/2 - (2 * i * totaldist/len(txts)) for i in range(len(txts)) ]
    return ' '.join([text(x, y - .5 - o, t, size, center = center) for t, o in zip(txts, offsets) ])

  npoints = [ floor((size[0] - args.margin[0] - args.binding - .000001) / args.grid), floor((size[1] - args.margin[1] - .000001) / args.grid) ]

  if args.dots > 0:
    print(f'Printing {npoints[0]}x{npoints[1]} grid')
  #  args.dots = papersize.parse_length(args.dots)
  #  npoints = [ floor(s / args.dots) for s in size ]
  #  xs = [ round((i + 1) * args.dots) for i in range(npoints[0]) ]
    # postscript has inverted y axis
  #  ys = [ round(size[1] - (i + 1) * args.dots) for i in range(npoints[1]) ]
    xs = [ getx(i) for i in range(npoints[0] + 1) ]
    ys = [ gety(i) for i in range(npoints[1] + 1) ]
    postscript = postscript + [ f'{x} {y} .5 0 360 arc closepath {args.gridgray} setgray fill' for x, y in [[x, y] for y in ys for x in xs ] ]
    f.write(' '.join(postscript))

  thirds = [ ceil((i + 1) * npoints[0] / 3) for i in range(2) ]
  fourths = [ round((i+1) * npoints[0] / 4) for i in range(3) ]

  if args.weekly:
    print('Printing weekly')
    weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    # week
    postscript = postscript + [ line(0, 4 * (i+1) - 1, npoints[0]) for i in range(3) ]
    postscript = postscript + [ line(thirds[0], 3, h=8), line(thirds[1], -1, h=12) ]
    zthirds = [0] + thirds
    postscript = postscript + [ text(zthirds[(i + 2) % 3], 4*floor((i+2) / 3), letter) for i, letter in enumerate(weekdays) ]
    postscript = postscript + [ h for hooks in [ hook(zthirds[(i + 2) % 3], 4*floor((i+2) / 3), 3) for i in range(len(weekdays)) ] for h in hooks ]
    # tasks
    postscript = postscript + [ text(i + .5, 12, letter, 6, center = True) for i, letter in enumerate(weekdays) ]
  #  postscript = postscript + [ text(i + .5, 12, ']', 6, center = True, rotate=90) for i in range(7) ]

    # review
    reviewheight = 5
    postscript = postscript + [ line(0, npoints[1] - 15 + i*reviewheight, w=npoints[0]) for i in range(3) ] # horizontal
    postscript = postscript + [ line(fourths[1], npoints[1] - 15, h=2*reviewheight) ] # vertical

    review = ['did you complete what\nyou set out to do?', 'does your calendar match up\nwith your priorities and values?']
    postscript = postscript + [ mtext(0, npoints[1] - 13 + i*reviewheight/2, t, center = False) for i, t in enumerate(review) ]

    review = ['clear out inbox', 'review meeting schedule', 'review past meetings', 'close all laptop tabs', 'close all phone tabs', 'clear out desktop', 'clear out downloads', 'clear off desk', 'move unfinished todos', 'delete > 2 week todos' ]
    postscript = postscript + [ b for boxes in [ box(fourths[1], npoints[1] - 15 + i) for i in range(len(review[:reviewheight])) ] for b in boxes ]
    postscript = postscript + [ text(fourths[1] + .6, npoints[1] - 14 + i, t) for i, t in enumerate(review[:reviewheight]) ]
    postscript = postscript + [ b for boxes in [ box(fourths[2], npoints[1] - 15 + i) for i in range(len(review[reviewheight:])) ] for b in boxes ]
    postscript = postscript + [ text(fourths[2] + .6, npoints[1] - 14 + i, t) for i, t in enumerate(review[reviewheight:]) ]

    review = ['what went well?', 'where did you get stuck?', 'what did you learn?' ]
    postscript = postscript + [ mtext(0, npoints[1] - 13.5 + reviewheight + 1.5*i, t, center = False) for i, t in enumerate(review) ]

    review = ['what are your long term goals?', 'do they still feel relevant?', 'what would make next\nweek a great week?' ]
    postscript = postscript + [ mtext(fourths[1], npoints[1] - 13.5 + reviewheight + 1.5*i, t, center = False) for i, t in enumerate(review) ]

    # next week
    postscript = postscript + [ line(x, npoints[1] - 5, h=6) for x in fourths ] + [ line(0, npoints[1] - 2, w = npoints[0]) ] # last is horizontal
    zfourths = [0] + fourths
    postscript = postscript + [ text(zfourths[i % 4] + .5 if i > 0 else 0, npoints[1] - 4 + 3*floor(i / 4), letter, center = i > 0) for i, letter in enumerate(['next week'] + weekdays) ]
    postscript = postscript + hook(0, npoints[1] - 4, 3.5)
    postscript = postscript + [ h for hooks in [ hook(zfourths[(i+1) % 4], npoints[1] - 4 + 3*floor((i+1) / 4), 1) for i in range(len(weekdays)) ] for h in hooks ]

#  postscript = postscript + [ line(fourths[0], npoints[1] - 4, h=8), line(thirds[1], -.5, h=11.5) ]
  elif args.daily:
    print('Printing daily')
    # lines
    postscript = postscript + [ line(0, 2*i, w=5.5) for i in range(5) ] + [ line(5, 0, h=10) ]
    postscript = postscript + [ mtext(2.5, 2, 'why do you\nfeel like that?'), mtext(2.5, 4, 'what can you do to\nhave more energy?'), mtext(2.5, 6, 'how do you define\na successful day?'), mtext(2.5, 8, 'what project to\nfocus on and why?'), mtext(2.5, 10, 'how can you\nmake a dent?') ]
    postscript = postscript + [ text(1.5, npoints[1] - 2, '___ : ___', center=True), text(3, npoints[1] - 2, 'what excited you today?'), text(3, npoints[1] - 1, 'what drained you of energy?'), text(3, npoints[1], 'what did you learn?') ]
    postscript = postscript + box(1, npoints[1] - 1.75, 3.5)

    # box
    postscript = postscript + [ line(npoints[0] - 4, 0, w=4), line(npoints[0] - 4, 0, h=4), line(npoints[0], 4, w=-4), line(npoints[0], 4, h=-4) ]
    postscript = postscript + [ line(npoints[0] - 4, 2, w=4, dash=True), line(npoints[0] - 2, 0, h=4, dash=True) ]
    postscript = postscript + [ text(npoints[0] - 2, 4.5, 'energy', 6, True), text(npoints[0] - 3.6, 2.65, 'focus', 6, True, 90) ]
    # horizontal
    postscript = postscript + [ text(npoints[0] - 4 + i, 4.45, '' if i == 2 else 2*i + 1, 4, True) for i in range(5) ]
    # vertical
    postscript = postscript + [ text(npoints[0] - 4.2, 4.25 - i, '' if i == 2 else 2*i + 1, 4, True) for i in range(5) ]

    # horizontal separator lines
    postscript = postscript + [ line(0, 10 + 10*i, w=npoints[0]) for i in range(2) ]
    # tasks
    postscript = postscript + [ line(x, 10, h=10, dash = i == 0) for i, x in enumerate(fourths) ]
    postscript = postscript + [ text(0, 11, 'TASKS', 7), text(fourths[1], 11, 'SHORT', 7), text(fourths[2], 11, 'MSG/SOCIAL', 7) ]
    postscript = postscript + hook(0, 11, 2.5) + hook(fourths[1], 11, 2.5) + hook(fourths[2], 11, 3.75)

    # day
    postscript = postscript + [ line(fourths[1], 20, h=npoints[1] - 23, dash=True) ]
    postscript = postscript + [ text(0, 21 + 2*i, args.daily + i, center = True) for i in range(floor((npoints[1] - 23) / 2)) ]
    # review section
    postscript = postscript + [ line(0, npoints[1] - 3, w=npoints[0]), line(3, npoints[1] - 3, h=3) ]

    f.write(f' showpage {args.binding - args.margin[0]/2} 0 translate {" ".join(postscript)} showpage')
    postscript = postscript + [ f' showpage {args.binding - args.margin[0]/2} 0 translate ' ] + postscript + [ ' showpage ' ]
#if isnamedsize: # FIXME does not work for 'landscape' sizes
#  gsspec = '-sPAPERSIZE=' + args.paper
#else:

#gsspec = f'-dDEVICEWIDTHPOINTS={round(size[0])} -dDEVICEHEIGHTPOINTS={round(size[1])}'
gsspec = f'-dDEVICEWIDTHPOINTS={size[0]} -dDEVICEHEIGHTPOINTS={size[1]}' # only accurate with -.2, -.5 WHY
os.system(f'gs -q {gsspec} -dBATCH -dNOPAUSE -sDEVICE={args.gsdevice} -sOutputFile={args.outfile} "{gsfile}"')
#os.system(f'gs -q {gsspec} -dBATCH -dNOPAUSE -sDEVICE={args.gsdevice} -sOutputFile={args.outfile} -c "{" ".join(postscript)}"')
