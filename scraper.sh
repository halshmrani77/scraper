#!/bin/bash
echo "Cron job started at `date`"
cd $( dirname "${BASH_SOURCE[0]}" )
python scraper.py
echo "Cron job completed at `date`"
