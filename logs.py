import re
import datetime
import os
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imageio

# https://github.com/quisquous/cactbot/blob/main/docs/LogGuide.md#ability-damage

#logFolder = "D:\\PikCeLL\\Documents\\TEST"
logFolder = "/home/elraine/Projects/ffxivprogressplotter/sourcelog"

fightID = "80037586"
phaseColors = ['b','r','y','g']
phases = [2.20,5.5,11.6,18.83]
phaseNames = ["LL", "BJCC", "Alex Prime", "Perfect"]

wipeRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000005.*")
clearRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000003.*")
startRegExp = re.compile(r"00\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|0039\|\|Engage!\|.*")

dmgRegExp = re.compile(r"^(?P<type>(?:2[12]))\|(?P<timestamp>(?:[^|]*))\|(?P<sourceId>(?:[^|]*))\|(?P<source>(?:[^|]*))\|(?P<id>(?:[^|]*))\|(?P<ability>(?:[^|]*))\|(?P<targetId>(?:[^|]*))\|(?P<target>(?:[^|]*))\|(?P<flags>(?:[^|]*))\|(?P<damage>(?:[^|]*))\|(?:[^|]*\|){14}(?P<targetCurrentHp>(?:[^|]*))\|(?P<targetMaxHp>(?:[^|]*))\|(?P<targetCurrentMp>(?:[^|]*))\|(?P<targetMaxMp>(?:[^|]*))\|(?:[^|]*\|){2}(?P<targetX>(?:[^|]*))\|(?P<targetY>(?:[^|]*))\|(?P<targetZ>(?:[^|]*))\|(?P<targetHeading>(?:[^|]*))\|(?P<currentHp>(?:[^|]*))\|(?P<maxHp>(?:[^|]*))\|(?P<currentMp>(?:[^|]*))\|(?P<maxMp>(?:[^|]*))\|(?:[^|]*\|){2}(?P<x>(?:[^|]*))\|(?P<y>(?:[^|]*))\|(?P<z>(?:[^|]*))\|(?P<heading>(?:[^|]*))\|")

minFrameDuration = 0.02
rampUpTime = 5
rampDownTime = 2
gifTime = 15


def damageNormalizer(bits):
	zfilled = bits.zfill(8)
	# print(f'''{zfilled}-{zfilled[4:6]}''')
	if zfilled[4:6] == '40':
		# print('LOTTA damage')
		# print(f'''{zfilled} zfilled''')
		# print(f'''{int(zfilled[2:4],base=16)}''')
		# print(f'''{int(zfilled[6:8],base=16)}''')
		# print(f'''{hex(int(zfilled[2:4],base=16) - int(zfilled[6:8],base=16))}''')

		# print(f'''{zfilled[6:8]}{zfilled[0:2]}{hex(int(zfilled[2:4],base=16)-int(zfilled[6:8],base=16))[2:]}''')
		# hex(int(zfilled[2:4],base=16)-int(zfilled[6:8],base=16))

		third = hex(int(zfilled[2:4],base=16) - int(zfilled[6:8],base=16))
		# print(third)
		if third[:1] == '-':
			third = hex(int('FF',base=16) + int(third,base=16))
		return int(f'''{zfilled[6:8]}{zfilled[0:2]}{third[2:]}''',base=16)
	else:
		# print('lol dmg')
		return int(zfilled[:4],base=16)
	# return int('424E400F'.zfill(8)[:4],base=16)
	# return int(bits.zfill(8)[:4],base=16)



def parseLog(logFile, dict, dmg):
	with open(logFile, 'r', encoding="utf8") as logSource:
		startTime = datetime.datetime(9999,12,31)
		endTime = datetime.datetime(1,1,1)
		clear = False
		for i, line in enumerate(logSource):
			startMatch = startRegExp.match(line)
			if startMatch:
				startTime = datetime.datetime(int(startMatch.group(1)),int(startMatch.group(2)),int(startMatch.group(3)),int(startMatch.group(4)),int(startMatch.group(5)),int(startMatch.group(6)))
			else:
				wipeMatch = wipeRegExp.match(line)
				if wipeMatch:
					endTime = datetime.datetime(int(wipeMatch.group(1)),int(wipeMatch.group(2)),int(wipeMatch.group(3)),int(wipeMatch.group(4)),int(wipeMatch.group(5)),int(wipeMatch.group(6)))
					clear = False
				else:
					clearMatch = clearRegExp.match(line)
					if clearMatch:
						endTime = datetime.datetime(int(clearMatch.group(1)),int(clearMatch.group(2)),int(clearMatch.group(3)),int(clearMatch.group(4)),int(clearMatch.group(5)),int(clearMatch.group(6)))
						clear = True
					else:
						dmgMatch = dmgRegExp.match(line)
						if dmgMatch: 
							print(f'''{dmgMatch.group('source')} - {dmgMatch.group('damage')} - {damageNormalizer(dmgMatch.group('damage'))}''')
						
			if endTime > startTime:
				duration = (endTime-startTime).total_seconds()/60
				dict[startTime] = (duration,clear)
				startTime = datetime.datetime(9999,12,31)
				endTime = datetime.datetime(1,1,1)

def parseFolder():
	timecontrol = SortedDict()
	dmg = dict()
	i = 1
	totalFiles = len(os.listdir(logFolder))
	for filename in os.listdir(logFolder):
		print(f"File {i} of {totalFiles}")
		i += 1
		parseLog(logFolder+"/"+filename,timecontrol, dmg)
	plt.xlabel("Pull #")
	plt.ylabel("Duration (min)")
	plt.figure(figsize=(16,9))
	adjustedPhases = [0] + phases
	for iPhase in range(len(phases)):
		plt.axhspan(adjustedPhases[iPhase], adjustedPhases[iPhase+1], facecolor=phaseColors[iPhase], alpha=0.1)
	filenames = []
	t = datetime.timedelta()
	wipecount = []
	wipecount = [0 for i in range(5)]
	
	
	rampUpIdx = len(dict)
	rampDownIdx = 0
	frameDuration = gifTime/len(dict)
	frameStep = 1
	if frameDuration < minFrameDuration:
		frameDuration = minFrameDuration
		rampUpIdx = rampUpTime/frameDuration
		rampDownIdx = rampDownTime/frameDuration
		frameStep = (len(dict) - rampUpIdx - rampDownIdx) / ((gifTime - rampUpTime - rampDownTime) / frameDuration)
	print(f"up {rampUpIdx}\ndown {rampDownIdx}\nstep {frameStep}")
	
	for j in range(len(dict)):
		# Dots
		if dict.peekitem(j)[1][1]:
			plt.plot(j, dict.peekitem(j)[1][0], color='yellow', marker='*', markeredgecolor='gray', markersize=10)
		else:
			plt.plot(j, dict.peekitem(j)[1][0], color='blue', marker='o', markersize=5)
		t += datetime.timedelta(seconds=int(dict.peekitem(j)[1][0]*60))
		plt.title(f"TEA prog : {j+1} pulls ({t} combat time)")
		
		# Legend
		patches = []
		counted = False
		for iPatch in range(len(phases)):
			if (not counted and dict.peekitem(j)[1][0] < phases[iPatch]):
				counted = True
				wipecount[iPatch] += 1
			patches += [mpatches.Patch(color=phaseColors[iPatch], label=(phaseNames[iPatch]) + f": {wipecount[iPatch]}")]
		plt.legend(handles=patches, loc="upper left")
		
		# create file name and append it to a list
		if j < rampUpIdx or j > (len(dict) - rampDownIdx) or (j - rampUpIdx)%int(frameStep) == 0:
			filename = f'{j}.png'
			filenames.append(filename)
			# save frame
			plt.savefig(filename)
		
	# build gif
	with imageio.get_writer('mygif.gif', format='GIF-PIL', mode='I', loop = 1, duration=frameDuration, subrectangles=True) as writer:
		for filename in filenames:
			image = imageio.imread(filename)
			writer.append_data(image)
	for filename in set(filenames):
		os.remove(filename)
	plt.show()

# print(damageNormalizer('424E400F'))
parseFolder()