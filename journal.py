#!/usr/local/bin/python3

import argparse
import papersize
import os

from math import ceil, floor

parser = argparse.ArgumentParser(description='generate daily/weekly/monthly journal pages on a dot-grid background')

parser.add_argument('-paper', default='180mmx257mm', help='paper size (named size or couple)')
parser.add_argument('-landscape', default=False, action='store_true')
parser.add_argument('-rightpage', default=False, action='store_true', help='shift page so that binding margin is on the left (relevant for monthly/yearly/weekly only)')
parser.add_argument('-margin', default='5mmx8.5mm', help='non-printable margin (length couple)') # was 5x7 (skipped bottom dot on print)
parser.add_argument('-binding', default='9mm', help='binding margin')
parser.add_argument('-dots', default=.5, help='grayscale intensity of the dot grid from 0 (black) to 1 (white)')
parser.add_argument('-grid', default='5mm', help='grid distance')

#parser.add_argument('-fromtop', action='store_true', help='place first grid element starting at the top (default is bottom)')
#parser.add_argument('-fromright', action='store_true', help='place first grid element starting on the right (default is left)')

parser.add_argument('-gray', type=float, default=.2, help='grayscale intensity of text and lines, from 0 (black) to 1 (white)')
parser.add_argument('-gridgray', type=float, default=.5, help='grayscale intensity of the dot grid from 0 (black) to 1 (white)')
parser.add_argument('-line', '-lw', default='.5pt', help='line stroke width (any named size)')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-daily', type=int, help='add daily page, starting the schedule at the given hour')
group.add_argument('-weekly', action='store_true', help='add daily page, starting the schedule at the given hour')
group.add_argument('-monthly', type=int, help='add monthly page for the given month (1-12)')
group.add_argument('-future', type=int, help='add future log double page starting in the given month')
group.add_argument('-yearly', action='store_true')
parser.add_argument('-year', type=int, help='year label to use in monthly and future log (defaults to the current year)')

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
#    f.write(r)
    return r

  hd = .22 # half diameter -- first print was .225
  def box(x, y, s = 1):
    r = [ line(x + .5 - s*hd, y + .5 - s*hd, w=2*s*hd), line(x + .5 - s*hd, y + .5 - s*hd, h=2*s*hd), line(x + .5 + s*hd, y + .5 - s*hd, h=2*s*hd), line(x + .5 - s*hd, y + .5 + s*hd, w=2*s*hd) ]
#    for s in r:
#      f.write(s)
    return r

#  def grid(x, y, dx, dy, offsets = []):
#    return None # TODO

  def hook(x, y, w): # a bottom right hook/box -- the y is one less to correspond to text
    return [ line(x+w, y-1, h=1), line(x, y, w=w) ]

  lastsize = None
  # x, y interpreted as the cell/row AFTER that line
  def text(x, y, txt, size = 8, center = False, rotate = 0, todo = False):
    global lastsize
    # https://stackoverflow.com/questions/27383154/how-do-i-get-ghostscript-to-load-ttf-fonts-globally
    ps = '' if size == lastsize else f'/Helvetica findfont {size} scalefont setfont  {args.gray} setgray '
    lastsize = size
    # TODO implement todo
    ps = ps + f'{getx(x) + (.2 if center else 5)} {gety(y) + 1.1*size/2} moveto ({txt}) {args.gray} setgray '
    if center:
      ps = ps + 'dup stringwidth pop 2 div neg 0 rmoveto'
    if rotate != 0:
      ps = ps + f' gsave {rotate} rotate show grestore '
    else:
      ps = ps + ' show '
#    f.write(ps)
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

  if args.rightpage and not args.daily:
    postscript = postscript + [f' {args.binding - args.margin[0]/2} 0 translate ']

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
    #f.write(' '.join(postscript))

  thirds = [ ceil((i + 1) * npoints[0] / 3) for i in range(2) ]
  fourths = [ round((i + 1) * npoints[0] / 4) for i in range(3) ]
  eighths = [ ceil((i + 1) * npoints[0] / 8) for i in range(7) ]

  from datetime import datetime
  now = datetime.now()
  if args.year == None:
    args.year = now.year
  import calendar

  weekdays = [x[0] for x in calendar.day_name]

  if args.yearly:
    postscript = postscript + [ text(0, 1.4, args.year, 16), text(17.5, 1, 'Specific / Measurable / Achievable / Relevant / Time-bound') ] +  hook(0, 1, 3)
    postscript = postscript + [ text(m-.5 + (m > 6)*(ceil(npoints[0]/2) - 6), 2, calendar.month_name[m][0], center=True) for m in range(1, 13) ]
    postscript = postscript + [ line(6, 1, h=npoints[1]-1, dash=True), text(6, 2, 'goals/sub-goals/dates'), line(17, 1, h=npoints[1]-1), line(23, 1, h=npoints[1]-1, dash=True), text(23, 2, 'goals/sub-goals/dates'), line(0, 2, w=npoints[0]) ]
    # put in quarter lines to space out goals/projects
    postscript = postscript + [ line(0, ceil(npoints[1]/2)+1, w=npoints[0], dash=True) ]
    # put 8 rows per month??
    postscript = postscript + [ line(5.5, 10, w=1, dash=True) ]
    postscript = postscript + [line(22.5, 10, w=1, dash=True)]
    postscript = postscript + [line(5.5, 18, w=1, dash=True)]
    postscript = postscript + [line(22.5, 18, w=1, dash=True)]
    postscript = postscript + [line(5.5, 34, w=1, dash=True)]
    postscript = postscript + [line(22.5, 34, w=1, dash=True)]
    postscript = postscript + [line(5.5, 42, w=1, dash=True)]
    postscript = postscript + [line(22.5, 42, w=1, dash=True)]

  elif args.future:
    print(123)
  elif args.monthly:
    postscript = postscript + [ text(0, .6, f'{calendar.month_name[args.monthly].upper()} {args.year}', 12) ] + hook(0, .5, len(calendar.month_name[args.monthly]) + 1.5)
    firstday, ndays = calendar.monthrange(args.year, args.monthly)
    postscript = postscript + [ line(-.5, 2, w=13.5), line(2, 1, h=ndays+1), text(3.5, 2, 'events', center=True), line(5, 1, h=ndays+1), text(9, 2, 'todos', center=True), line(13, 1, h=ndays+1) ]
    for i in range(1, ndays+1):
      postscript = postscript + [ text(.5, 2 + i, i, center=True), text(1.5, 2 + i, weekdays[(firstday + i) % 7], center=True) ]
      if (firstday + i) % 7 == 6:
        postscript = postscript + [ line(-.5, 2 + i, w=13.5) ]

    postscript = postscript + [ text(13, 2, 'GOALS') ] + hook(13, 2, 2.5)

  elif args.weekly:
    print('Printing weekly')
    # put binding margin on left instead
    #postscript = [ f'{args.binding - args.margin[0]/2} 0 translate ' ] + postscript

    # week
    if True:
        themes = ['', '', '', '', '', ' (rest day)', ' (big pic+read)']
        postscript = postscript + [ line(x, -1, h=12) for x in eighths ]
        postscript = postscript + [ line(eighths[0], 0, npoints[0]-eighths[0]) ]
        postscript = postscript + [ text(eighths[i], 0, letter + themes[i]) for i, letter in enumerate(weekdays) ]
        postscript = postscript + [ line(0, 11, npoints[0]) ]
        postscript = postscript + [ line(0, 12, 7) ]
    else: # old style
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
    postscript = postscript + [ line(1.5 if i % 2 else 0, npoints[1] - 15 + i*reviewheight, w=npoints[0]-3.5 if i % 2 else npoints[0]) for i in range(3) ] # horizontal
    postscript = postscript + [ mtext(0, npoints[1] - 9.1, 'past', 6, False), mtext(npoints[0] - 1, npoints[1] - 9.1, 'future', 6) ] #, 6, True, 90

    postscript = postscript + [ line(fourths[1], npoints[1] - 14.25, h=2*reviewheight-1.5) ] # vertical
    postscript = postscript + [ mtext(npoints[0]/2-2, npoints[1] - 13.75, 'execution', 6), mtext(npoints[0]/2-.5, npoints[1] + reviewheight - 9.5, 'reflection', 6) ]

    review = ['what did I complete?', 'what was my best day?', 'biggest time wasters?', "what did I do that I hadn't planned?"]
    postscript = postscript + [ mtext(0, npoints[1] - 13.5 + i, t, center = False) for i, t in enumerate(review) ]

    review = ['clear out inbox', 'clear out desktop', 'clear out downloads', 'clear off desk', 'close all laptop tabs', 'close all phone tabs', 'move unfinished todos', 'delete > 2 week todos', 'dump new todos/ideas', 'check calendar/events' ]
    postscript = postscript + [ b for boxes in [ box(fourths[1], npoints[1] - 15 + i) for i in range(len(review[:reviewheight])) ] for b in boxes ]
    postscript = postscript + [ text(fourths[1] + .6, npoints[1] - 14 + i, t) for i, t in enumerate(review[:reviewheight]) ]
    postscript = postscript + [ b for boxes in [ box(fourths[2], npoints[1] - 15 + i) for i in range(len(review[reviewheight:])) ] for b in boxes ]
    postscript = postscript + [ text(fourths[2] + .6, npoints[1] - 14 + i, t) for i, t in enumerate(review[reviewheight:]) ]

    review = ['what worked well?', 'where did I get stuck?', 'what did I learn?' , 'did I impact anyone?', "what's on my NOT-do list?"]
    postscript = postscript + [ mtext(0, npoints[1] - 13.5 + reviewheight + 1*i, t, center = False) for i, t in enumerate(review) ]

    prospect = ['re-visit long-term goals', 'pick <= 3 active projects' ]
    postscript = postscript + [ b for boxes in [ box(fourths[1 + i], npoints[1] - 10) for i in range(len(prospect)) ] for b in boxes ]
    postscript = postscript + [ text(fourths[1 + i] + .6, npoints[1] - 9, t) for i, t in enumerate(prospect) ]

    review = ['am I making progress on my BHAGs?', 'what would make next\nweek a great week?' ]
    postscript = postscript + [ mtext(fourths[1], npoints[1] - 12.5 + reviewheight + 1.5*i, t, center = False) for i, t in enumerate(review) ]

    # next week
    postscript = postscript + [ line(x, npoints[1] - 5, h=6) for x in fourths ] + [ line(0, npoints[1] - 2, w = npoints[0]) ] # last is horizontal
    zfourths = [0] + fourths
    postscript = postscript + [ text(zfourths[i % 4] + .5 if i > 0 else 0, npoints[1] - 4 + 3*floor(i / 4), letter, center = i > 0) for i, letter in enumerate(['next week'] + weekdays) ]
    postscript = postscript + hook(0, npoints[1] - 4, 3.5)
    postscript = postscript + [ h for hooks in [ hook(zfourths[(i+1) % 4], npoints[1] - 4 + 3*floor((i+1) / 4), 1) for i in range(len(weekdays)) ] for h in hooks ]
#  postscript = postscript + [ line(fourths[0], npoints[1] - 4, h=8), line(thirds[1], -.5, h=11.5) ]
  elif args.daily:
    print('Printing daily')

    # review section
    postscript = postscript + [ line(0, 4, w=npoints[0]), line(3, -1, h=5), line(0, 0, w=3) ]
    preview = ['what excited me today?', 'what drained me of energy?', 'what did I learn?', 'how did I push the needle forward?', "tomorrow's FROG:" ]
    postscript = postscript + [ text(1.5, 0, 'REVIEW', 7, center=True), text(1.5, 1, '___ : ___', center=True) ] + [ text(3, i, t) for i, t in enumerate(preview) ]
    postscript = postscript + box(-.5, 1) + [ text(.2, 2, 'success?', 7) ]
    postscript = postscript + box(-.5, 2) + [ text(.2, 3, 'tidy tasks', 7) ]

    # shift down
    postscript = postscript + [ f'gsave 0 {-5*args.grid} translate' ]

    # lines
    postscript = postscript + [ line(0, 2*i, w=5.5) for i in range(5) ] + [ line(5, 0, h=10) ]
    postscript = postscript + [ mtext(2.5, 2, 'why do you\nfeel like that?'), mtext(2.5, 4, 'what can you do to\nhave more energy?'), mtext(2.5, 6, 'how do you define\na successful day?'), mtext(2.5, 8, 'what project to\nfocus on and why?'), mtext(2.5, 10, 'how can you\nmake a dent?') ]

    # box
    postscript = postscript + [ line(npoints[0] - 4, 0, w=4), line(npoints[0] - 4, 0, h=4), line(npoints[0], 4, w=-4), line(npoints[0], 4, h=-4) ]
    postscript = postscript + [ line(npoints[0] - 4, 2, w=4, dash=True), line(npoints[0] - 2, 0, h=4, dash=True) ]
    postscript = postscript + [ text(npoints[0] - 2, 4.5, 'energy', 6, True), text(npoints[0] - 3.6, 2.65, 'focus', 6, True, 90) ]
    # horizontal
    postscript = postscript + [ text(npoints[0] - 4 + i, 4.45, '' if i == 2 else 2*i + 1, 4, True) for i in range(5) ]
    # vertical
    postscript = postscript + [ text(npoints[0] - 4.2, 4.25 - i, '' if i == 2 else 2*i + 1, 4, True) for i in range(5) ]

    # horizontal separator lines
    postscript = postscript + [ line(0, 10, w=npoints[0]) ] # top line
    postscript = postscript + [ line(0, 10+9, w=npoints[0]) ] # food line
    postscript = postscript + [ line(0, 10+10, w=npoints[0]) ] # bottom line
    # tasks
    postscript = postscript + [ line(x, 10, h=10, dash = i != 2) for i, x in enumerate(thirds) ]
    postscript = postscript + [ text(0, 11, 'TASKS', 7), text(thirds[1], 11, 'SHORT/MSG/SOCIAL', 7) ]
    postscript = postscript + hook(0, 11, 2.5) + hook(thirds[1], 11, 5.5)
    # day
    postscript = postscript + [ line(2, 20, h=npoints[1] - 26, dash=False) ] # 'time blocking' line
    postscript = postscript + [ line(fourths[1], 20, h=npoints[1] - 26, dash=True) ] # middle line
    postscript = postscript + [ text(0, 21 + 2*i, args.daily + i, center = True) for i in range(ceil((npoints[1] - 25) / 2)) ]
    # check-in goal
    postscript = postscript + [ line(0, npoints[1] - 6, w=npoints[0]) ]
    postscript = postscript + [ text(1, npoints[1] - 5, 'check-in:', center=True) ]

    postscript = postscript + [ 'grestore' ]

#    f.write(f' showpage {args.binding - args.margin[0]/2} 0 translate {" ".join(postscript)} showpage')
    postscript = [ f'gsave {args.binding - args.margin[0]/2} 0 translate ' ] + postscript + [ ' showpage grestore' ] + postscript + [ ' showpage ' ]
#if isnamedsize: # FIXME does not work for 'landscape' sizes
#  gsspec = '-sPAPERSIZE=' + args.paper
#else:

with open(gsfile, 'w') as f:
  for cmd in postscript:
    f.write(cmd)
    f.write(' ')

#gsspec = f'-dDEVICEWIDTHPOINTS={round(size[0])} -dDEVICEHEIGHTPOINTS={round(size[1])}'
gsspec = f'-dDEVICEWIDTHPOINTS={size[0]} -dDEVICEHEIGHTPOINTS={size[1]}' # only accurate with -.2, -.5 WHY
os.system(f'gs -q {gsspec} -dBATCH -dNOPAUSE -sDEVICE={args.gsdevice} -sOutputFile={args.outfile} "{gsfile}"')
#os.system(f'gs -q {gsspec} -dBATCH -dNOPAUSE -sDEVICE={args.gsdevice} -sOutputFile={args.outfile} -c "{" ".join(postscript)}"')
