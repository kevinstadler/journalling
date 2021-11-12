## bullet journalling template pages

default paper size (`180mmx257mm`) is JIS B5, a common format for lose-leaf binders/notebooks

* some 26 hole B5: 173x251
* Senmu 'B5' notebook: 173x253
* ISO B5: 176x250
* Benmu 'B5' 18K080-0913B(A): 178x254mm
* rounded-corner Daolian: 180x256
* JIS B5: 182x257

### example usage

generate a daily page, starting at 8 am (this prints a double page, left then right): `./journal.py -daily 8 daily.pdf`

generate a weekly page (left page only): `./journal.py -weekly weekly.pdf`

```
usage: journal.py [-h] [-paper PAPER] [-landscape] [-margin MARGIN]
                  [-binding BINDING] [-dots DOTS] [-grid GRID] [-gray GRAY]
                  [-gridgray GRIDGRAY] [-line LINE] [-daily DAILY] [-weekly]
                  [-gsdevice GSDEVICE]
                  outfile

generate boxes of similar colors

positional arguments:
  outfile               the file to write the test page to

optional arguments:
  -h, --help            show this help message and exit
  -paper PAPER          paper size (named size or couple)
  -landscape
  -margin MARGIN        non-printable margin (length couple)
  -binding BINDING      binding margin
  -dots DOTS            grayscale intensity of the dot grid from 0 (black) to
                        1 (white)
  -grid GRID            grid distance
  -gray GRAY            grayscale intensity of text and lines, from 0 (black)
                        to 1 (white)
  -gridgray GRIDGRAY    grayscale intensity of the dot grid from 0 (black) to
                        1 (white)
  -line LINE, -lw LINE  line stroke width (any named size)
  -daily DAILY          add daily page, starting the schedule at the given
                        hour
  -weekly               add daily page, starting the schedule at the given
                        hour
  -gsdevice GSDEVICE    one of pdfwrite, eps2write etc, see https://www.ghosts
                        cript.com/doc/current/Devices.htm#High-level
```
