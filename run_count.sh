# !/bin/bash

echo "Results summary:"
echo "---------------------------------"
echo "|           | IMO problems | JGEX problems |"
echo "---------------------------------"
echo "| AlphaGeometry | $(ls output/alphageometry/imo | wc -l)          | $(ls output/alphageometry/jgex | wc -l)           |"
echo "---------------------------------"
echo "| DDAR         | $(ls output/ddar/imo | wc -l)          | $(ls output/ddar/jgex | wc -l)           |"
echo "---------------------------------"
