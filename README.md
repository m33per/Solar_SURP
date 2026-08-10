# Solar_SURP

This project is meant to analyze the data from energy production by Cal Poly's solar farm in order to determine where energy output is reduced due to shading by neighboring solar panels.

If possible, this project also aims to find new angles for the solar panels such that they track the sun as optimally as possible without casting shade on other panels. They actually already aim to do this, but the algorithm they follow does not account for the uneven terrain they stand on.

Creating a tool now:

implement later:
be able to pull data
-maybe just stick with monthly divisions

basic page:
select inverters and a day to view graph
select inverter and days to view graph
select irradiance and a days to view graph

sunset page:
select month, get list of days that are likely uncloudy by irradiance
pick a day, run code and identify shady areas

config page:
select which days to save (or delete) as good days
for each month, alter thresholds for bad slope and concavity
for each month, alter beginning sunset end ending sunrise times
