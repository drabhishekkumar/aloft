#!/usr/bin/env python

import os, sys

def writeBed(vcfInputPath, outputPath):
	inputFile = open(vcfInputPath)
	outputFile = open(outputPath, "w")

	counter = 1

	for line in inputFile:
		if line.startswith("#"):
			continue

		fields = line.strip().split("\t")
		chromosome = fields[0]
		startPos = int(fields[1])
		ref = fields[3]
		alts = fields[4].split(",")

		for altIndex, alt in enumerate(alts):
			if len(ref) > len(alt):
				# deletion event
				diff = ref[0:len(alt)]
				endPos = startPos + len(diff)
				#indelCall = '-' + diff
			elif len(alt) > len(ref):
				diff = alt[0:len(ref)]
				endPos = startPos
				#indelCall = '+' + diff
			else:
				endPos = startPos
				#indelCall = "."

			outputFile.write("\t".join([chromosome, str(startPos-1), str(endPos), str(counter)]) + "\n")
			counter += 1
	inputFile.close()
	outputFile.close()

if __name__ == "__main__":
	writeBed(sys.argv[1], sys.argv[2])