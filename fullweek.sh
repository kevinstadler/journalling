#!/bin/sh
pdftk A="weekly.pdf" B="daily.pdf" cat A B2 B B B output "fullweek.pdf"
