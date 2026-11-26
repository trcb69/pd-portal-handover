import re,json,collections
PRE=re.compile(r'^\s*(SP|CP|SH|DP|RTP|PRINTSERV|PACKSERV|Service|Sub)\s*[-:]\s*',re.I)
DIM=r'\d+(?:\.\d+)?\s?(?:cm|mm|inch|in|")?\s?[xX×]\s?\d+(?:\.\d+)?\s?(?:cm|mm|inch|in|")?(?:\s?[xX×]\s?\d+(?:\.\d+)?\s?(?:cm|mm|inch|in|")?)?'
SIZE=re.compile('('+DIM+r'|\d+(?:\.\d+)?\s?(?:oz|ml|ltr|l|g|kg|gsm|pcs|pc)\b|\d+(?:\.\d+)?\s?(?:inch|mm|cm)\b)',re.I)
COL=['black','white','brown','kraft','red','blue','green','gold','silver','yellow','pink','orange','purple','grey','gray','clear','transparent','natural','ivory','cream','maroon','navy']
FIN=['glossy','gloss','matt','matte','lamination','laminated','varnish','spot uv','uv','embossed','foil','soft touch']
WALL=['s/wall','d/wall','r/wall','single wall','double wall','ripple wall','double','single','ripple']
MAT=['paper','plastic','pp','pet','pe coated','pe','poly','polybond','aluminium','aluminum','foil','corrugated','e flute','b flute','board','bagasse','pla','cpla','cardboard','ivory board','pvc']
FEAT=['window','lid','liner','handle','divider','dividers','with window','with lid','with liner','sleeve','holder','tray','insert','flap','clasp']
def parse(name):
    n=PRE.sub('',name.strip()); tags=re.findall(r'\(([^()]*)\)\s*$',n)
    base=re.sub(r'\s*\([^()]*\)\s*$','',n)
    a={}; rest=base
    m=SIZE.findall(rest)
    if m: a['Size']=' / '.join(dict.fromkeys(x.strip() for x in m)); rest=SIZE.sub(' ',rest)
    low=rest.lower()
    def pick(lst,key,rest):
        found=[w for w in lst if re.search(r'(?<![a-z])'+re.escape(w)+r'(?![a-z])',rest.lower())]
        found=[w for w in found if not any(w!=o and w in o for o in found)]
        if found:
            a[key]=', '.join(w.title() if '/' not in w else w.upper() for w in found)
            for w in found: rest=re.sub(re.escape(w),' ',rest,flags=re.I)
        return rest
    rest=pick(WALL,'Wall',rest); rest=pick(FIN,'Finish',rest); rest=pick(COL,'Colour',rest); rest=pick(FEAT,'Feature',rest); rest=pick(MAT,'Material',rest)
    fam=re.sub(r'[^a-z0-9]+',' ',rest.lower()).strip()
    return a,fam,(tags[-1] if tags else '')
