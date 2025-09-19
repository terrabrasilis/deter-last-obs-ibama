# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 14:06:43 2020

@author: Luis Maurano
"""
import requests
import psycopg2
from bs4 import BeautifulSoup
import re
import os
from datetime import date

#define mes-ano
ano_mes = date.today().strftime("%Y_%m")
datai = str(ano_mes.replace('_', '-')) + "-01"

#define bioma
bioma = os.getenv("TARGET_BIOME")
assert bioma

# Data directory for writing downloaded data
DIR=os.path.realpath(os.path.join(os.path.dirname(__file__),"../data/"))
DIR=os.getenv("DATA_DIR", DIR)
assert DIR

output = f"{DIR}/{bioma}/" # setar aqui novo path

# database params
host=os.getenv("PGHOST")
database=os.getenv("PGDB")
port=os.getenv("PGPORT")
user=os.getenv("PGUSER")
password=os.getenv("PGPASSWORD")
assert host
assert database
assert port
assert user
assert password

con = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
assert con

#conecta BD em funcao do bioma
tabledeter = None
if bioma == 'Amazonia':
    tabledeter = 'deter_agregate.deter'
    
if bioma == 'Cerrado':
    tabledeter = 'aggregate.deter'

assert tabledeter

# the base URL of download page service
BASE_URL="http://cbers9.dpi.inpe.br:8089/files"
BASE_URL=os.getenv("BASE_URL", BASE_URL)
# used to test in localhost where the cbers9 is unreachable
proxies = {
"http": "http://localhost:3128",
"https": "https://localhost:3128",
}
#recupera conteudo do diretorio CB4
listdir = []

# cria lista dos diretorios das imagens CB4, CB4A e Amz
def lista_dir(url):
    page = requests.get(url=url) #, proxies=proxies) # Getting page HTML through request
    soup = BeautifulSoup(page.content, 'html.parser') # Parsing content using beautifulsoup

    links = soup.select("a") # Selecting all of the anchors with titles
    topDirs = links[1:len(links)-1] # Keep only the first 1 anchors (NGInX = 1) (Apache = 5)
    pattern="/"
    for anchor in topDirs:
        match = re.search(pattern, anchor.text)
        if(match):
            listdir.append(anchor.text)
        
url = f'{BASE_URL}/CBERS4/'+ano_mes # para CB4
lista_dir(url)

url = f'{BASE_URL}/CBERS4A/'+ano_mes # para CB4A
lista_dir(url)

url = f'{BASE_URL}/AMAZONIA1/'+ano_mes # para CB4A
lista_dir(url)

#print(listdir)

#sql para buscar imagens usadas no periodo
sql = "SELECT satellite, orbitpoint, view_date, count(id) FROM " + tabledeter
sql += " where view_date >= '"+ datai + "'" 
#sql += " AND view_date <= (date_trunc('month', '" + datai + "'::date) + interval '1 month' - interval '1 day')::date"
sql +=  " AND  view_date <= view_date- INTERVAL '-15 days'" 
#sql +=  " AND  view_date <= '"+ dataf + "'" 
sql += " AND satellite IN ('AMAZONIA-1','CBERS-4A','CBERS-4')"
sql += " group by satellite, orbitpoint, view_date order by view_date asc"

cur = con.cursor()
cur.execute(sql)
campos = cur.fetchall()
print(bioma, sql)

for campo in campos:
    pathrow = str(campo[1])
    pathrow  = pathrow.replace('_', '')   
    path =  pathrow[0:3]
    #path = path.zfill(3)
    row =  pathrow[3:6]
    #row = row.zfill(3)
    path_row =  path + '_' + row
    satelite = campo[0]
    view_date = str(campo[2])
    ano_mes_dia = view_date.replace('-', '_')
    anomesdia = view_date.replace('-', '')
    ano_mes = ano_mes_dia[0:7]
    anomes =  view_date[:4] + '_' + view_date[5:7]
    
    if bioma == 'Cerrado':
        pathrow = str(campo[1]) #036_016
        aux = pathrow.split("_")
        path = aux[0].zfill(3)
        row = aux[1].zfill(3)
        path_row =  path + '_' + row
    
    aux = satelite.split("-")
    satelite = aux[0] + "_" +aux[1]
    
    sensor = "AWFI"
    pasta = satelite.replace('_', '')
    formato = "DRD"
    projecao = "UTM"
    
    if satelite == "AMAZONIA_1":
        projecao = "LCC"
    
    if satelite == "CBERS_4A" or satelite == "AMAZONIA_1":
        sensor = "WFI"
        formato = "RAW"
        
    nometif = satelite + "_" + sensor + "_" + anomesdia + "_" + path_row + "_L4_CMASK_GRID_SURFACE.tif"
    name = satelite + "_" + sensor + "_" + formato + "_" + ano_mes_dia
    #print(name)
    
    for item in listdir:
        url = f"{BASE_URL}/" + pasta + "/" + ano_mes + "/" + item + "/" + path_row + "_0/4_BC_" + projecao + "_WGS84/" + nometif
        #print (url)
        if name in item:
            output_directory = output + nometif
            #print(output_directory)

            try:
                file = 1
                myfile = requests.get(url=url) #, proxies=proxies)
                if myfile.ok:
                    open(output_directory, 'wb').write(myfile.content)
                newfile =  output  + nometif
                os.rename(output_directory, newfile)
                #print (nometif + " ENCONTRADA \n \n")
                
                # cataloga imagem na tabela 
                tifname = nometif
                tif_split = tifname.split("_")
                #print(tif_split)
                sat = tif_split[0] + "_" + tif_split[1]
                sensor = tif_split[2]
                data = tif_split[3]
                pathrow = tif_split[4] + tif_split[5]
                
                try: # armazena imagem que foi feita download
                    query = "INSERT INTO public.cmask_acervo (bioma, source, satellite, sensor, data, pathrow, processada)  VALUES ('" + bioma + "', '" + tifname + "', '" + sat + "', '" + sensor + "', '" + data + "', '" + pathrow + "', " + str(0) + ")"
                    cur.execute(query)
                    con.commit()
                    print('inseriu ' + tifname )
                except Exception:
                    print('tiff ja inserido ' + tifname )
                    con.rollback()
                
                
            except:
                file = 0
                #print (url + " nao encontrada \n \n")
            

