#!/bin/sh
pdftk A="weekly.pdf" B="daily.pdf" cat B1 A B B B output "fullweek.pdf"
