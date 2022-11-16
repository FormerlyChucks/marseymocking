import yaml
import requests
import random
import os
import traceback
from urllib.parse import urlencode


with open("/home/xxx/marseymocking/config.yaml") as configyaml:#change this
    config = yaml.safe_load(configyaml)

IMGFLIPUSERNAME = config["IMGFLIPUSERNAME"]
IMGFLIPPASSWORD = config["IMGFLIPPASSWORD"]
TEMPLATEID = config["TEMPLATEID"]
TEMPLATEURL = config["TEMPLATEURL"]
RDRAMATOKEN = config["RDRAMATOKEN"]
RDRAMAUSERNAME = config["RDRAMAUSERNAME"]
RDRAMAPASSWORD = config["RDRAMAPASSWORD"]
CHOICES = config["CHOICES"]
POSTCOMMENT_URL = config["POSTCOMMENT_URL"]
COMMENTS_URL = config["COMMENTS_URL"]
BANNED_IDS = config["BANNED_IDS"]
COMMENT_URL = config["COMMENT_URL"]
RDRAMAHEADERS = {"Authorization": RDRAMATOKEN}

def get_parent_comment(cid):
    cid = str(cid)
    response = requests.get(COMMENT_URL.format(cid), headers = RDRAMAHEADERS)
    if response.status_code == 429:
        raise requests.exceptions.RequestException()
    elif response.status_code != 200:
        raise BaseException(f"POST {COMMENT_URL.format(cid)} ({response.status_code}) => {response.json()}")
    else:
        r = response.json()
        return (r["body"],r["author_name"])
    
def generate_meme(text):
    params = {
        "username": IMGFLIPUSERNAME,
        "password": IMGFLIPPASSWORD,
        "template_id": TEMPLATEID,
        "boxes[0][text]": "",
        "boxes[1][text]": text,
    }
    response = requests.post(TEMPLATEURL, params = params).json()
    url = response['data']['url']
    return url

def mocking_text(text):
    text = text.lower()
    mockingtext = ""
    for letter in text:
        choice = random.choice(CHOICES)
        if choice == 'YES':
            l = letter.lower()
        elif choice == 'NO':
            l = letter.upper()
        else:
            l = letter
        mockingtext += l
    return mockingtext

def download_meme(url):
    response = requests.get(url)
    filename = '/tmp/'+url.split('/')[-1]
    with open(filename, 'wb') as f:
        f.write(response.content)
    return filename

def delete_meme(path):
    os.remove(path)
    return

def make_comment(parent_fullname, parent_submission, file, text):
    parent_fullname = str(parent_fullname)
    if 't3_' not in parent_fullname:
        parent_fullname = 't3_'+parent_fullname
    data = {'parent_fullname': parent_fullname,
            'submission': parent_submission,
            'body': text
           }
    with open(file, 'rb') as commentfile:
        filedata = {'name': file.replace('/tmp/',''),
                    'binary': commentfile,
                    'type': 'image/jpg'
                   }
        cf = {'file': (filedata['name'], filedata['binary'], filedata['type'])}
        response = requests.post(POSTCOMMENT_URL, headers=RDRAMAHEADERS, data=data, files=cf)
    if response.status_code == 429:
        raise requests.exceptions.RequestException()
    if response.status_code != 200:
        raise BaseException(f"POST {POSTCOMMENT_URL} ({response.status_code}) {data} => {response.json()}")
    else:
        return response.json()
    
def comment_check(comment):
    good = True
    with open("/home/xxx/marseymocking/ids.txt") as idsread:
        ids = [int(line.rstrip()) for line in idsread.readlines()]
    commentid = int(comment["id"])
    if commentid in ids:
        good = False
        quit()
    with open("/home/xxx/marseymocking/ids.txt", "a") as idswrite:#and this
        idswrite.write(f"{commentid}\n")
    if comment["author"]["id"] in BANNED_IDS:
        good = False
        return good
    if comment["is_bot"] == True:
        good = False
        return good
    if comment["level"] == 1:
        good = False
        return good
    if comment["body"].lower().replace("!","").replace("#","") != ":marseymocking:":
        good = False
        return good
    else:
        good = {'id':comment["id"],
                'author_id':comment["author"]["id"],#??why??
                'parent_comment_id':comment["parent_comment_id"],
                'post_id':comment["post_id"],
                'body':comment["body"]}
        return good
    
def get_comments():
    page = 1
    while True:
        try:
            response = requests.get(COMMENTS_URL.format(page), headers=RDRAMAHEADERS)
            if response.status_code == 429:
                raise requests.exceptions.RequestException()
            elif response.status_code != 200:
                raise BaseException(f"POST {COMMENTS_URL} ({response.status_code}) => {response.json()}")
            else:
                r = response.json()["data"]
                for comment in r:
                    check = comment_check(comment)
                    if check:
                        checkid = check["id"]
                        parent_comment_id = check["parent_comment_id"]
                        post_id = check["post_id"]
                        body = check["body"]
                        gcb = get_parent_comment(parent_comment_id)
                        mt = mocking_text(gcb[0])
                        gm = generate_meme(mt)
                        dm = download_meme(gm)
                        mc = make_comment(checkid,post_id,file=dm,text="@"+str(gcb[1]))
                        print('replied to',checkid)
                        delete_meme(path=dm)
            print('done with page:',page)
            page += 1
        except Exception:
            print(traceback.format_exc())
            quit()

get_comments()
