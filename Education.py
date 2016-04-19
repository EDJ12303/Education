# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 19:34:11 2016

@author: Erin
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import sqlite3 as lite
import csv
import math
import statsmodels.api as sm
import numpy as np
import matplotlib as plt

url = "http://web.archive.org/web/20110514112442/http://unstats.un.org/unsd/demographic/products/socind/education.htm"

r = requests.get(url)
soup = BeautifulSoup(r.content, 'lxml')

#get all rows ('tr') 
rows = soup.find_all('tr')[18:-11]
print rows

#Create a table with the country name, the male school life expectancy, the female school life expectancy and the year of the analysis
#make a dataframe that contains the necessary data
df_school = pd.DataFrame(columns=['country', 'year', 'male_sle', 'female_sle'])


#add values to the dataframe
i = 0
for row in rows:
	col = row.findAll('td')
	# The columns for country, year, male_sle, and female_sle are in indices 0,1,7,10
	df_school.loc[i] = [(col[0].text).encode('ascii', 'ignore'),int(col[1].text),int(col[7].text),int(col[10].text)]
	i += 1

#set "country" as the dataframe index
df_school = df_school.set_index('country')

print df_school
# convert to csv 
df_school.to_csv('school.csv', header=True)
######################################################################
##STATISTICS ON SCHOOL LIFE EXPECTANCY##

df_school['male_sle'] = df_school['male_sle'].astype(float)
df_school['female_sle'] = df_school['female_sle'].astype(float)

print ("The mean values for the Male SLE and Female SLE are:" )
print (df_school['male_sle'].mean())
print ("and")
print (df_school['female_sle'].mean())

print ("The median values for the Male SLE and Female SLE are:" )
print (df_school['male_sle'].median())
print ("and")
print (df_school['female_sle'].median())

#median is likely the more appropriate value for interpreting data#
#########################################################################


# create sqlite3 database
con = lite.connect('SchoolGDP.db')
cur = con.cursor()

# Drop tables if they already exist
with con:
    cur.execute("DROP TABLE IF EXISTS school")
# create table to hold school info
with con:
    cur.execute('CREATE TABLE school (country TEXT PRIMARY KEY, _Year numeric, _MYears numeric, _FYears numeric)')

# populate school years table
with open('school.csv') as inputFile:
    header = next(inputFile)
    inputReader = csv.reader(inputFile)
    for line in inputReader:
        schoolGDP = [line[0], line[1], line[2], line[3]]
        with con:
            cur.execute('INSERT INTO school (country, _Year, _MYears, _FYears) VALUES (?, ?, ?, ?);', schoolGDP)



# Drop tables if they already exist
with con:
    cur.execute("DROP TABLE IF EXISTS GDP")    
# create table to hold gdpinfo data
with con:
    cur.execute('CREATE TABLE GDP (country TEXT PRIMARY KEY, _1999 float, _2000 float, _2001 float, _2002 float, _2003 float, _2004 float, _2005 float, _2006 float, _2007 float, _2008 float, _2009 float, _2010 float)')
    
#Get GDP data from World Bank zip file and insert into gdp table
with open('GDP.csv') as inputFile:
    next(inputFile) # skip the first four lines
    next(inputFile)
    next(inputFile)
    next(inputFile)
    header = next(inputFile)
    inputReader = csv.reader(inputFile)
    for line in inputReader:
        with con:
            cur.execute('INSERT INTO GDP (country, _1999, _2000, _2001, _2002, _2003, _2004, _2005, _2006, _2007, _2008, _2009, _2010) VALUES ("' + line[0] + '","' + '","'.join(line[43:-6]) + '");')
            
with con:    
    cur = con.cursor()    
    cur.execute("SELECT * FROM GDP")

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    df_GDP= pd.DataFrame(rows, columns=cols)
    print df_GDP


# convert gdp to floats
df_GDP.convert_objects(convert_numeric=True).dtypes

# convert gdp to log in order to scale properly
log_GDP = math.log(df_GDP)

# The dependent variable
y = log_GDP

# The independent variable
x = df_GDP['country']

#create linear model
X = sm.add_constant(x)
model = sm.OLS(y,X)
f = model.fit()
# output results summary
print f.summary()




