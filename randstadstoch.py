from pcraster import *
from pcraster.framework import *

class MyFirstModel(DynamicModel, MonteCarloModel):
  def __init__(self):
    DynamicModel.__init__(self)
    MonteCarloModel.__init__(self)
    setclone('randstad.map')
    
  def premcloop(self):
    pass
    
  def initial(self):
    self.dist = readmap("dist.map")
    randstad = readmap("randstad.map")
    self.counter = 0
    self.countertracker = scalar(randstad)*0
    self.report(self.countertracker, "countertracker1")

    #classes van bestaande map worden samengevoegd tot 6 bestaande classes
    bebouwing = (randstad == 10) | (randstad == 11) | (randstad == 12) | (randstad == 20) | (randstad == 21) | (randstad == 22)| (randstad == 23) | (randstad == 24)| (randstad == 30) | (randstad == 31) | (randstad == 32)| (randstad == 33) | (randstad == 35)
    samengevoegd1 = ifthenelse(bebouwing, 1, randstad)

    landbouw = (randstad == 50) | (randstad == 51)
    samengevoegd2 = ifthenelse(landbouw, 6, samengevoegd1)

    natuur = (randstad == 60) | (randstad == 61) | (randstad == 62)
    samengevoegd3 = ifthenelse(natuur, 3, samengevoegd2)

    semibebouwd = (randstad == 34)
    samengevoegd4 = ifthenelse(semibebouwd, 4, samengevoegd3)

    recreatie = (randstad == 40) | (randstad == 41) | (randstad == 42)| (randstad == 43) | (randstad == 44) | (randstad == 45)
    samengevoegd5 = ifthenelse(recreatie, 5, samengevoegd4)
    
    water = (randstad == 70) | (randstad == 71) | (randstad == 72) | (randstad == 73) | (randstad == 74) | (randstad == 75)| (randstad == 76) | (randstad == 77)| (randstad == 78) | (randstad == 80) | (randstad == 81)| (randstad == 82) | (randstad == 83)
    randstadfinal = ifthenelse(water, 2, samengevoegd5)

    aguila(randstadfinal)
    self.report(randstadfinal, "randstadfinal")
    #legend(open("legendafile.txt", "r"), randstadfinal) #past legenda toe via console

    self.isbebouwd = randstadfinal == 1
    self.islandbouw = randstadfinal == 6
    self.isnatuur = randstadfinal == 3
    self.issemi = randstadfinal == 4
    self.isrecreatie = randstadfinal == 5
    self.iswater= randstadfinal == 2

    #wat reports for troubleshooten
    #report(self.islandbouw, "landb")
    #report(self.isbebouwd, "bebouw")
    #aguila(self.islandbouw)
    
  def dynamic(self):
    #neighbourhood data for the different classes
    nrofbebouwdneighbours = windowtotal(scalar(self.isbebouwd), celllength()*3)
    nroflandbouwneighbours = windowtotal(scalar(self.islandbouw), celllength()*3)
    nrofnatuurneighbours = windowtotal(scalar(self.isnatuur), celllength()*3)
    nrofsemineighbours = windowtotal(scalar(self.issemi), celllength()*3)
    nrofrecreatieneighbours = windowtotal(scalar(self.isrecreatie), celllength()*3)
    nrofwaterneighbours = windowtotal(scalar(self.iswater), celllength()*3)

    #tussentijds report voor trouble shooten
    report(nrofbebouwdneighbours, "nrb")

    #transition rules implementeren
    #nrofneighbours is nu zo gedaan dat ze allemaal een soort weeging hebben in hoe erg ze de kans op bebouwing vergroten/verkleinen
    kansopsemi = scalar((nrofbebouwdneighbours*0.3+nrofrecreatieneighbours*0.15+nrofsemineighbours*0.2)/2)-(self.dist/400000)
    #min kans op 0 zetten
    kansgecorrigeerd = ifthenelse(kansopsemi < 0, scalar(0), kansopsemi)
    self.report(kansgecorrigeerd, "kans")

    #eerste check om te kijken of die het kans treshhold haalt
    uni=uniform(1)*55
    check = ifthenelse(kansgecorrigeerd >= uni, boolean(1), boolean(0))
    self.report(check, "check")

    #checken of die wel landbouw is
    check2 = ifthenelse(pcrand(check, self.islandbouw), boolean(1), boolean(0))
    self.report(check2, "check2")


    #de semi en landbouw kaart aanpassen
    self.issemi = ifthenelse(pcror(check2, self.issemi),boolean(1), boolean(0))
    self.islandbouw = ifthenelse(self.issemi, boolean(0), self.islandbouw)
    self.report(self.islandbouw, "landb")
    self.report(self.issemi, "semi")

    #semi naar bebouwd counter code hieronder
    self.countertracker = ifthenelse(pcrand(self.issemi, self.countertracker == 0),scalar(self.counter), self.countertracker)
    
    self.counter += 1
    self.report(self.countertracker, "tracker")

    uni2 = uniform(1)*2
    self.isbebouwd = ifthenelse(pcrand(self.issemi, (self.counter-self.countertracker >= 3+uni2)), boolean(1), self.isbebouwd)
    self.report(self.isbebouwd, "bebouw")

    #hier zorgen we ervoor dat als iets naar bebouwd flipt die van semi weg gaat
    self.issemi = ifthenelse(self.isbebouwd, boolean(0), self.issemi)
    self.report(self.issemi, "semi")

    #dit rekened dus je total area van de bebouwd class uit
    totalarea = areatotal(scalar(self.isbebouwd), self.isbebouwd)
    self.report(totalarea, "area")

    #voegt alle kaartjes samen en maakt er een eind nominal kaart van
    randstadendgame = nominal(scalar(self.issemi)*4+scalar(self.isbebouwd)*1+scalar(self.islandbouw)*6+scalar(self.iswater)*2+scalar(self.isnatuur)*3+scalar(self.isrecreatie)*5)
    self.report(randstadendgame, "endgame")

    
  def postmcloop(self):
    #gebruikt total area als input en berekend verschillende statistieken
    names=["area"]
    sampleNumbers=self.sampleNumbers()
    timeSteps=self.timeSteps()
    percentiles=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]


    #The function mcaveragevariance calculates the mean and variance of realizations, on a cell-by-cell basis.
    #average(names, sampleNumbers)
    mcaveragevariance(names,sampleNumbers,timeSteps)
    mcpercentiles(names,percentiles,sampleNumbers,timeSteps)


nrOfSamples = 10
nrOfTimeSteps = 50
myModel = MyFirstModel()
dynamicModel = DynamicFramework(myModel, nrOfTimeSteps)
mcModel = MonteCarloFramework(dynamicModel, nrOfSamples)
mcModel.run()
