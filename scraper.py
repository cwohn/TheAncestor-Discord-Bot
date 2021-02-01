import requests
from bs4 import BeautifulSoup
import pprint
import copy
import re

URL = "https://darkestdungeon.gamepedia.com/Narrator"
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
#print(soup.prettify())


#Take an ogg_source tag
#     <source scr="..." type="application/ogg>
# and find the transcript of the audio
def get_transcript(ogg_source):
    #Go up to find the <span> tag
    span_tag = ogg_source.find_parent("span")
    if span_tag is None:
        print("No span...")
        return None

    #Go forward to find the <table> tag
    table_tag = span_tag.find_previous("table")
    if table_tag is None:
        print("No table...")
        return None
     
    #Go down to find the <tr> tag
    tr_tag = table_tag.find("tr")
    if tr_tag is None:
        print("No tr")
        return None

    #Go down to find the right <td> tag
    #The right <td> tag has no style attribute 
    td_tag = tr_tag.find(lambda tag:tag.name=="td" and
                                    not tag.has_attr("style"))
    if td_tag is None:
        print("No td")
        return None

    #Finally, get all the text in the td tag
    #To do this, find all tags and replace them with their children
    #So that only a string remains
    #Then remove any \" in the string
    string = copy.copy(td_tag)
    for tag in string.find_all(True):
        tag.replaceWithChildren()
    if string is None:
        print("No string")
        return None
    if string.text is None:
        print("No text")
        return None
    string = string.text.replace("\"","")
    return string

##Get all links to sound files
##Downlod the file to snd/filename.ogg
##Write the transcript to txt/filename.txt
#
#e.g. <source src="www.website/folder/.../foo/Vo_narr_stuff_03.ogg/bar/.../">
#     --> Vo_narr_stuff_03.ogg
#         Vo_narr_stuff_03.txt

#Pre-define a regex to extract the filename
filename_pattern = re.compile("[A-Za-z0-9_]*\.ogg")

#Loop through <source type="application/ogg"> tags
for ogg_source in soup.find_all("source",type="application/ogg"):
    #Get the URL of the file
    src_url = ogg_source.get("src")

    #Get the filename
    filename = re.search(filename_pattern, src_url).group(0)
    
    #download audio file
    file = requests.get(src_url)
    with open("snd/"+filename,"wb") as f:
        f.write(file.content)

    #Create a file for the transcript
    transcript = get_transcript(ogg_source)
    with open("txt/"+filename.replace(".ogg",".txt"),"w") as f:
        f.write(transcript)
    

