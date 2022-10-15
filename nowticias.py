from requests import Request, Session
import random
import concurrent.futures
from xml.dom import minidom
from bs4 import BeautifulSoup
from flask import jsonify
from flask_caching import Cache
from flask_executor import Executor
from flask import (
    Flask,
    render_template,
    request
)

NUM_NEWS_PER_SITE = 6

G1_GERAL = "https://g1.globo.com/rss/g1/"
G1_ECONOMIA = "https://g1.globo.com/rss/g1/economia/"
G1_POLITICA = "https://g1.globo.com/rss/g1/politica/"
G1_TECH = "https://g1.globo.com/rss/g1/tecnologia/"

EXAME_GERAL = "https://exame.com/feed/"
EXAME_TECH = "https://exame.com/tecnologia/feed/"
EXAME_ECONOMIA = "https://exame.com/economia/feed/"
EXAME_POLITICA = "https://exame.com/brasil/feed/"

VEJA_GERAL = "https://veja.abril.com.br/feed/"
VEJA_TECH = "https://veja.abril.com.br/tecnologia/feed/"
VEJA_ECONOMIA = "https://veja.abril.com.br/economia/feed/"
VEJA_POLITICA = "https://veja.abril.com.br/politica/feed/"

GIZMODO = "https://gizmodo.uol.com.br/feed/"

TECMUNDO = "https://rss.tecmundo.com.br/feed"

CANALTECH = "https://canaltech.com.br/rss/"

INFO_MONEY = "https://www.infomoney.com.br/feed/"

CORREIO_GERAL = "https://www.correiobraziliense.com.br/rss/noticia/brasil/rss.xml"
CORREIO_POLITICA = "https://www.correiobraziliense.com.br/rss/noticia/politica/rss.xml"
CORREIO_ECONOMIA = "https://www.correiobraziliense.com.br/rss/noticia/economia/rss.xml"
CORREIO_TECH = "https://www.correiobraziliense.com.br/rss/noticia/tecnologia/rss.xml"

R7_GERAL = "https://noticias.r7.com/feed.xml"
R7_TECH = "https://noticias.r7.com/tecnologia-e-ciencia/feed.xml"
R7_ECONOMIA = "https://noticias.r7.com/economia/feed.xml"
R7_POLITICA = "https://noticias.r7.com/politica/feed.xml"

UOL_GERAL = "http://rss.home.uol.com.br/index.xml"
UOL_TECH = "http://rss.uol.com.br/feed/tecnologia.xml" 
UOL_ECONOMIA = "http://rss.uol.com.br/feed/economia.xml"
UOL_ENTRETENIMENTO = "http://rss.uol.com.br/feed/entretenimento.xml"

OLHAR_DIGITAL_GERAL = "https://olhardigital.com.br/rss"

GAZETA_GERAL = "https://www.gazetadopovo.com.br/feed/rss/republica.xml"
GAZETA_ECONOMIA = "https://www.gazetadopovo.com.br/feed/rss/economia.xml"

ELPAIS_GERAL = "https://feeds.elpais.com/mrss-s/pages/ep/site/brasil.elpais.com/portada"

CARTA_GEGRAL = "https://www.cartacapital.com.br/feed/"

VALOR_ECONOMICO = "https://www.valor.com.br/rss"

TUDO_CELULAR = "https://www.tudocelular.com/feed/"

INTERCEPT_GERAL = "https://theintercept.com/feed/?lang=pt"

JOVEMPAN_GERAL = "https://jovempan.com.br/feed"
JOVEMPAN_ENTRETENIMENTO = "https://jovempan.com.br/entretenimento/feed"
JOVEMPAN_POLITICA = "https://jovempan.com.br/brasil/feed"

MEGA_CURIOSO = "http://rss.megacurioso.com.br/feed"

PAPEL_POP = "https://www.papelpop.com/feed/"

JOVEM_NERD = "https://jovemnerd.com.br/feed/"

#MINUTO_GERAL = "https://www.noticiasaominuto.com.br/rss/ultima-hora"
#MINUTO_ECONOMIA = "https://www.noticiasaominuto.com.br/rss/economia"


def isValidValue(value):
    return value != "" and not value.isspace() and not "VÍDEOS:" in value 

def getItens(theme):
    xml = Session().get(theme)
    xml = minidom.parseString(xml.text)    
    rss = xml._get_firstChild()

    if theme == VALOR_ECONOMICO:
        rss = xml._get_childNodes()[1]

    channel = rss._get_childNodes()

    if "r7.com" in theme:
        return channel

    for i in range(0, len(channel)):
        if channel[i].nodeName == "channel":
            channel = channel[i]
            break
    return channel._get_childNodes()

def getDefaultNews(args):
    try:
        theme = args[0]
        site = args[1]
        news = []
        itens = getItens(theme)

        firstNode = 1
        step = 2

        if site == "Correio Braziliense" or site == "Tecmundo" or site == "Mega Curioso":
            firstNode = 0
            step = 1

        for i in range(firstNode, len(itens) , step):
            item = itens[i]._get_childNodes()

            title, link, description, image = "", "", "", ""
            
            for j in range(firstNode, len(item), step):
                try:
                    if item[j].nodeName == "title":
                        title = item[j]._get_firstChild().data
                        if theme == VALOR_ECONOMICO:
                            title = title.encode('latin').decode('utf-8')
                        #if "</" in title or "/>" in title or "<p>" in title or "<br" in title:
                        #    title = BeautifulSoup(title, "html.parser").text.split("\n")[0]
                    elif item[j].nodeName == "link" or item[j].nodeName == "url":
                        if isValidSite(item[j]._get_firstChild().data):
                            link = item[j]._get_firstChild().data
                    elif item[j].nodeName == "description" or item[j].nodeName == "subtitle" or item[j].nodeName == "content":
                        for value in item[j]._get_childNodes():
                            if theme == UOL_TECH or theme == UOL_ECONOMIA or theme == PAPEL_POP:
                                try:
                                    image = BeautifulSoup(value.data, "html.parser").contents[0].attrs['src']
                                except:
                                    pass
                            elif site == "Canaltech" or site == "InfoMoney":
                                try:
                                    image = BeautifulSoup(value.data, "html.parser").contents[0].contents[0].attrs['src']
                                except:
                                    pass
                            if not isValidValue(description):
                                description = value.data
                                if theme == VALOR_ECONOMICO:
                                    description = description.encode('latin').decode('utf-8')

                                if "</" in description or "/>" in description or "<p>" in description or "<br" in description:
                                    # Exame tratamento
                                    description = BeautifulSoup(description, "html.parser").text.split("\n")[0]
                    elif item[j].nodeName == "media:content" or item[j].nodeName == "media:thumbnail" or item[j].nodeName == "enclosure":
                        image = item[j].getAttribute('url')
                    elif item[j].nodeName == "content:encoded":
                        if site == "Jovem Pan" or site == "Gizmodo" or site == "Tudo Celular":
                            value = item[j]._get_firstChild()
                            image = BeautifulSoup(value.data, "html.parser")
                            image = image.contents[0]
                            if site == "Jovem Pan":
                                image = image.contents[0]
                            if site == "Tudo Celular":
                                image = image.attrs['href']
                            else:
                                image = image.attrs['src']
                    elif item[j].nodeName == "mediaurl" or item[j].nodeName == "image" or item[j].nodeName == "urlImage":
                        if "http" not in image and "www" not in image:
                            image = item[j]._get_firstChild().data
                except Exception as e:
                    pass
            
            if isValidValue(title) and isValidValue(link) and isValidValue(description) and isValidValue(image):
                current_news = {
                    "title": "" + site + ": " + title.lstrip().replace("\"", "\'").replace("[", "(").replace("]", ")")[0:200],
                    "url": link,
                    "description": description.lstrip().replace("\"", "\'").replace("[", "(").replace("]", ")")[0:200],
                    "image": image,
                    "site": site
                }
                news.append(current_news)
            
            if len(news) == NUM_NEWS_PER_SITE:
                return news
        # Nao atingiu o numero minimo, alguma treta rolou: site mudou? Me enviar email
        return news
    except:
        return None

geralList = [
    [G1_GERAL, "G1"],
    [EXAME_GERAL, "Exame"],
    [CORREIO_GERAL, "Correio Braziliense"],
    [R7_GERAL, "R7"],
    [UOL_GERAL, "UOL"],
    [OLHAR_DIGITAL_GERAL, "Olhar Digital"],
    [VEJA_GERAL, "Veja"],
    [ELPAIS_GERAL, "El País"],
    [INTERCEPT_GERAL, "The Intercept"],
    [JOVEMPAN_GERAL, "Jovem Pan"],
    [TECMUNDO,"Tecmundo"]
]

techList = [
    [TUDO_CELULAR, "Tudo Celular"],
    [GIZMODO, "Gizmodo"],
    [TECMUNDO,"Tecmundo"],
    [CANALTECH, "Canaltech"],
    [EXAME_TECH, "Exame"],
    [UOL_TECH, "UOL"],
    [OLHAR_DIGITAL_GERAL, "Olhar Digital"]
]

economyList = [
    [UOL_ECONOMIA, "UOL"],
    [GAZETA_ECONOMIA, "Gazeta do Povo"],
    [CORREIO_ECONOMIA, "Correio Braziliense"],
    [G1_ECONOMIA, "G1"],
    [EXAME_ECONOMIA, "Exame"],
    [VEJA_ECONOMIA, "Veja"],
    [R7_ECONOMIA, "R7"]
]

entertainmentList = [
    [JOVEMPAN_ENTRETENIMENTO, "Jovem Pan"],
    [UOL_ENTRETENIMENTO, "UOL"],
    [PAPEL_POP, "Papel POP"],
    [MEGA_CURIOSO, "Mega Curioso"]
]

politicList = [
    [INTERCEPT_GERAL, "The Intercept"],
    [GAZETA_GERAL, "Gazeta do Povo"],
    [G1_POLITICA, "G1"],
    [R7_POLITICA, "R7"],
    [CORREIO_POLITICA, "Correio Braziliense"],
    [VEJA_POLITICA, "Veja"],
    [EXAME_POLITICA, "Exame"],
    [JOVEMPAN_POLITICA, "Jovem Pan"]
]

validSites = [
    "uol.com.br", 
    "elpais.com", 
    "g1.globo.com", 
    "correiobraziliense.com.br", 
    "gazetadopovo.com.br",
    "veja.abril.com.br",
    "exame.com",
    "olhardigital.com.br",
    "noticias.r7.com",
    "theintercept.com",
    "jovempan.com",
    "tecmundo.com",
    "canaltech.com",
    "infomoney.com",
    "valor.com.br",
    "tudocelular.com",
    "megacurioso.com",
    "papelpop.com"
]

def isValidSite(site):
    for item in validSites:
        if item in site:
            return True
    return False

def generateNewsList(executor, sitesList):
    sitesDict = {}
    output = []
    
    # DEBUG 
    #for item in sitesList:
    #   sitesDict[item[1]] = getDefaultNews(item)

    for args, news in zip(sitesList, executor.map(getDefaultNews, sitesList)):
        try:
            if news != None:
                sitesDict[args[1]] = news
        except:
            pass

    keys =  list(sitesDict.keys())
    random.shuffle(keys)
    while len(sitesDict) > 0:
        for key in keys:
            if key in sitesDict:
                if len(sitesDict[key]) == 0:
                    del sitesDict[key]
                else:
                    output.append(sitesDict[key].pop(0))

    return jsonify(output)
    

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
executor = Executor(app) 

# DEBUG
#generateNewsList(executor, politicList)
# Especifico
#a = getDefaultNews([JOVEMPAN_GERAL, "Jovem Pan"])

@app.route('/getNews/<theme>', methods=['GET', 'POST'])
#@cache.cached(timeout=1800)
def getNews(theme):
    if 'Authorization' in request.headers:
        if request.headers['Authorization'] != "Key bm93dGljaWFzOmVSNTk0RXlkWWdIekNiZ2ZWWjdO":
            return jsonify(["eUnauthorizedrro"]), 401
        else:
            if theme == "geral":
                return generateNewsList(executor, geralList)
            elif theme == "tech":
                return generateNewsList(executor, techList)
            elif theme == "economia":
                return generateNewsList(executor, economyList)
            elif theme == "politica":
                return generateNewsList(executor, politicList)
            else:
                return jsonify(["Theme not informed"])
    else:
        return jsonify(["Unauthorized"]), 401


@app.route('/status', methods=['GET', 'POST'])
def getStatus():
    return "Oie"

if __name__ == "__main__":
    app.run(host='0.0.0.0')

"""
import blip_session
blipSession = BlipSession(BOT_AUTHORIZATION)
"""
