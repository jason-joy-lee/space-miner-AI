from dataclasses import dataclass
from random import Random
from math import dist

@dataclass(frozen=True)
class Planet:
    id: str
    thermal: float
    spectral: float
    ore: bool

def galaxy(seed=42):
    rng=Random(seed)
    def make(prefix, count):
        out=[]
        for i in range(count):
            x,y=round(rng.uniform(0,10),2),round(rng.uniform(0,10),2)
            ore=min(dist((x,y),(2.5,7.5)),dist((x,y),(7.5,3.0)))<=2.4
            if rng.random()<.10: ore=not ore
            out.append(Planet(f"{prefix}-{i+1:02}",x,y,ore))
        return out
    for _ in range(100):
        starter=make("TR",8)
        if len(set(p.ore for p in starter))==2: break
    else: raise RuntimeError("Could not create mixed starter set")
    return dict(starter=starter,reserve=make("SC",6),validation=make("VA",20),mining=make("PX",12))

def knn(training, candidate, k):
    if not training or k<1 or k>len(training) or k%2==0: raise ValueError("K must be odd and fit training data")
    closest=sorted(training,key=lambda p:(dist((p.thermal,p.spectral),(candidate.thermal,candidate.spectral)),p.id))[:k]
    votes=sum(p.ore for p in closest)
    return votes>k//2,closest,votes

def accuracy(training, validation, k):
    if not validation: raise ValueError("Validation must not be empty")
    return sum(knn(training,p,k)[0]==p.ore for p in validation)/len(validation)

def baseline(training,validation):
    majority=sum(p.ore for p in training)>len(training)/2
    return sum(p.ore==majority for p in validation)/len(validation)

def mine(credits, mined, planet):
    if planet.id in mined: raise ValueError("Already mined")
    if len(mined)>=5: raise ValueError("Five-mine limit")
    if credits<10: raise ValueError("Insufficient credits")
    return credits-10+(25 if planet.ore else 0), mined|{planet.id}
