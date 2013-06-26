import sys, os, re, string, array, datetime, gerprate
import networkx as nx
from optparse import OptionParser
from subprocess import Popen, PIPE
from vat_run import *
import collections
from sequencing import *
from aloft_common import *

print "Starting at: " + datetime.datetime.now().strftime("%H:%M:%S")

stdin=sys.stdin

##NMD threshold (premature STOP to last exon-exon junction)
dist = 50

#Build command line arguments options
parser = OptionParser()

#Add options and default values-
options = collections.OrderedDict([('vcf', ''),\
                                   ('annotation_interval', 'data/gencode.v16.pc.interval'),\
                                   ('annotation_sequence', 'data/gencode.v16.pc.fa'),\
                                   ('vat', 'output/vat_output.vcf'),\
                                   ('tabbed_output_lof', 'output/tabbed_output_lof'),\
                                   ('tabbed_output_splice', 'output/tabbed_output_splice'),\
                                   ('vcf_output', 'output/output.vcf'),\
                                   ('elements', 'data/elements/'),\
                                   ('annotation', 'data/gencode.v16.annotation.gtf'),\
                                   ('rates', 'data/bases/'),\
                                   ('gerp_cache', 'gerp_cache/'),\
                                   ('genome', 'data/genome/'),\
                                   ('ancestor', 'data/homo_sapiens_ancestor_GRCh37_e71/'),\
                                   ('segdup', 'data/hg19-segdup.txt'),\
                                   ('thousandG', 'data/ALL.wgs.phase1_release_v3.20101123.snps_indels_sv.sites.gencode16.SNPS.vat.vcf'),\
                                   ('exomes', 'data/ESP6500/'),\
                                   ('ensembl_table', 'data/ens67_gtpcgtpolymorphic.txt'),\
                                   ('protein_features', 'data/prot-features/'),\
                                   ('transmembrane', 'data/tm_ens70/'),\
                                   ('ppi', 'data/BIOGRID-ORGANISM-Homo_sapiens-3.2.95.tab.txt'),\
                                   ('recessive_genes', 'data/science_lofpaper_omim_recessive_filtered.list'),\
                                   ('dominant_genes', 'data/dominantonly.list'),\
                                   ('haplo_score', 'data/imputed.hi.scores'),\
                                   ('LOF_score', 'data/prob_recessive_disease_scores.txt'),\
                                   ('netSNP_score', 'data/Supplementary_Table8.20Jul2012.txt'),\
                                   ('pseudogenes', 'data/gencode.v7.pgene.parents'),\
                                   ('paralogs', 'data/within_species_geneparalogs.ens70'),\
                                   ('dNdS', 'data/dNdS_avgs.txt'),\
                                   ('disopred_sequences', 'data/disopred_sequences'),
                                   ('phosphorylation', 'data/phosphorylation')])

help = {'vcf' : 'Path to vcf input file. This can be a compressed .gz file',\
        'annotation_interval' : 'Path to annotation interval file for VAT (default is %s)' % (options['annotation_interval']),\
        'annotation_sequence' : 'Path to annotation sequence file for VAT (default is %s)' % (options['annotation_sequence']),\
        'vat' : 'Path to VAT output file. (default is %s)' % (options['vat']),\
        'tabbed_output_lof' : 'Path to tab-delimited output file for lof (default is %s)' % (options['tabbed_output_lof']),\
        'tabbed_output_splice' : 'Path to tab-delimited output file for splice (default is %s)' % (options['tabbed_output_splice']),\
        'vcf_output' : 'Path to VCF output file (default is %s)' % (options['vcf_output']),\
        'elements' : 'Path to directory containing hg19_chr*_elems.txt files (default is %s)' % (options['elements']),\
        'annotation' : 'Path to .gtf annotation file (default is %s)' % (options['annotation']),\
        'rates' : 'Path to directory containing chr*.maf.rates files (default is %s)' % (options['rates']),\
        'gerp_cache' : 'Output to directory for gerp cache files (default is %s, directory is created if it does not exist)' % (options['gerp_cache']),\
        'genome' : 'Path to directory containing chr*.fa files (default is %s)' % (options['genome']),\
        'ancestor' : 'Path to directory containing homo_sapiens_ancestor_*.fa files (default is %s)' % (options['ancestor']),\
        'segdup' : 'Path to segdup annotation file (default is %s)' % (options['segdup']),\
        'thousandG' : 'Path to 1000G file (default is %s)' % (options['thousandG']),\
        'exomes' : 'Path to directory containing ESP6500.chr*.snps.vcf files (default is %s)' % (options['exomes']),\
        'ensembl_table' : 'Path to transcript to protein lookup table file (default is %s)' % (options['ensembl_table']),\
        'protein_features' : 'Path to directory containing chr*.prot-features-ens70.txt files (default is %s)' % (options['protein_features']),\
        'transmembrane': 'Path to directory containing transmembrane chr*.tmsigpcoilslc.ens70.txt (default is %s)' % (options['transmembrane']),\
        'ppi' : 'Path to protein-protein interaction network file (default is %s)' % (options['ppi']),\
        'recessive_genes' : 'Path to list of recessive genes (default is %s)' % (options['recessive_genes']),\
        'dominant_genes' : 'Path to list of dominant genes (default is %s)' % (options['dominant_genes']),\
        'haplo_score' : 'Path to haploinsufficiency disease scores (default is %s)' % (options['haplo_score']),\
        'LOF_score' : 'Path to LOF disease scores (default is %s)' % (options['LOF_score']),\
        'netSNP_score' : 'Path to netSNP disease scores (default is %s)' % (options['netSNP_score']),\
        'pseudogenes' : 'Path to pseudogenes file (default is %s)' % (options['pseudogenes']),\
        'paralogs' : 'Path to paralogs file (default is %s)' % (options['paralogs']),\
        'dNdS' : 'Path to dNdS file (default is %s)' % (options['dNdS']),\
        'disopred_sequences' : 'Path to disopred sequences (default is %s)' % (options['disopred_sequences']),\
        'phosphorylation' : 'Path to directory containing ptm.phosphorylation.chr*.txt files (default is %s)' % (options['phosphorylation'])}

for key, value in options.iteritems():
    parser.add_option('', '--'+key, action='store', type='string', dest=key+'_path', default=value, help=help[key])

(options, args) = parser.parse_args()

shouldSkipVAT = False
if options.vcf_path == '': # try to skip VAT
    if not os.path.exists(options.vat_path):
        parser.print_help()
        print "A VCF file was not supplied by the --vcf option"
        sys.exit(1)
    else:
        print "\nNo VCF file has been passed in with the --vcf option."
        print "Running ALoFT on %s" % (options.vat_path) + "\n"
        shouldSkipVAT = True

if not shouldSkipVAT: #run VAT
    if not os.path.exists(options.vcf_path):
        parser.print_help()
        print "VCF file %s not found!" % (options.vcf_path)
        sys.exit(1)

    if not os.path.exists(options.annotation_interval_path):
        parser.print_help()
        print "Annotation interval file %s not found!" % (options.annotation_interval_path)
        sys.exit(1)

    if not os.path.exists(options.annotation_sequence_path):
        parser.print_help()
        print "Annotation sequence file %s not found!" % (options.annotation_sequence_path)
        sys.exit(1)

    run_vat([sys.argv[0], options.vcf_path, options.vat_path, options.annotation_interval_path, options.annotation_sequence_path])

try:
    infile=open(options.vat_path)
except:
    parser.print_help()
    print options.vat_path + ' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

try:
    o_lof=open(options.tabbed_output_lof_path, 'w')
except:
    parser.print_help()
    print options.tabbed_output_lof_path + ' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

try:
    o_splice=open(options.tabbed_output_splice_path, 'w')
except:
    parser.print_help()
    print options.tabbed_output_splice_path + ' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

try:
    o2=open(options.vcf_output_path, 'w')
except:
    parser.print_help()
    print options.vcf_output_path + ' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

genomepath = options.genome_path

try:
    annotfile=open(options.annotation_path)
except:
    parser.print_help()
    print options.annotation_path + ' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

ancespath = options.ancestor_path

GERPratepath = options.rates_path

#this is for caching gerp score files for optimization
GERPratecachepath = options.gerp_cache_path
if not os.path.exists(GERPratecachepath):
    #try to create the directory
    try:
        os.mkdir(GERPratecachepath)
    except:
        parser.print_help()
        print "ERROR: Failed to create gerp cache directory at %s" % (GERPratecachepath)
        sys.exit(1)

GERPelementpath = options.elements_path

segduppath = options.segdup_path
try:
    segdupfile=open(segduppath)
except:
    parser.print_help()
    print segduppath+' could not be opened.'
    #print 'Exiting program.'
    sys.exit(1)

thousandGPath = options.thousandG_path
try:
    thousandGInputFile = open(thousandGPath)
except:
    parser.print_help()
    print thousandGPath + " could not be opened."
    sys.exit(1)

exomeDirectory = options.exomes_path
if not os.path.exists(exomeDirectory):
    parser.print_help()
    print exomeDirectory + " directory could not be found"
    sys.exit(1)

transcriptToProteinFilePath = options.ensembl_table_path
if not os.path.exists(transcriptToProteinFilePath):
    parser.print_help()
    print transcriptToProteinFilePath + " could not be found"
    sys.exit(1)

proteinfeaturesDirectory = options.protein_features_path
if not os.path.exists(proteinfeaturesDirectory):
    parser.print_help()
    print proteinfeaturesDirectory + " could not be found"
    sys.exit(1)

transmembraneDirectory = options.transmembrane_path
if not os.path.exists(transmembraneDirectory):
    parser.print_help()
    print transmembraneDirectory + " could not be found"
    sys.exit(1)

phosphorylationDirectory = options.phosphorylation_path
if not os.path.exists(phosphorylationDirectory):
    parser.print_help()
    print phosphorylationDirectory + " could not be found"
    sys.exit(1)

ppipath = options.ppi_path
try:
    ppifile=open(ppipath)
except:
    parser.print_help()
    print ppipath+' could not be opened.'
    sys.exit(1)

rgenespath = options.recessive_genes_path
try:
    rgenesfile=open(rgenespath)
except:
    parser.print_help()
    print rgenespath+' could not be opened.'
    sys.exit(1)

dgenespath = options.dominant_genes_path
try:
    dgenesfile=open(dgenespath)
except:
    parser.print_help()
    print dgenespath+' could not be opened.'
    sys.exit(1)

haploscorepath = options.haplo_score_path
try:
    haploscorefile=open(haploscorepath)
except:
    parser.print_help()
    print haploscorepath+' could not be opened.'
    sys.exit(1)

LOFscorepath = options.LOF_score_path
try:
    LOFscorefile=open(LOFscorepath)
except:
    parser.print_help()
    print LOFscorepath+' could not be opened.'
    sys.exit(1)

netSNPscorepath = options.netSNP_score_path
try:
    netSNPscorefile=open(netSNPscorepath)
except:
    parser.print_help()
    print netSNPscorepath+' could not be opened.'
    sys.exit(1)

pseudogenespath = options.pseudogenes_path
try:
    pseudogenesfile=open(pseudogenespath)
except:
    parser.print_help()
    print pseudogenespath+' could not be opened.'
    sys.exit(1)

paralogspath = options.paralogs_path
try:
    paralogsfile=open(paralogspath)
except:
    parser.print_help()
    print paralogspath+' could not be opened.'
    sys.exit(1)

dNdSpath = options.dNdS_path
try:
    dNdSfile=open(dNdSpath)
except:
    parser.print_help()
    print dNdSpath+' could not be opened.'
    sys.exit(1)

disopredSequencesPath = options.disopred_sequences_path
if not os.path.exists(disopredSequencesPath):
    parser.print_help()
    print disopredSequencesPath+' could not be found.'
    sys.exit(1)

chrs = [`i` for i in range(1, 23)]
chrs.append('X')
chrs.append('Y')

def getAncestors(ancespath):
    ## Coordinates for chromosomes are 1-based.
    ancestor={}
    for i in chrs:
        try:
            f=open(os.path.join(ancespath, 'homo_sapiens_ancestor_'+i+'.fa'))
        except:
            print os.path.join(ancespath, 'homo_sapiens_ancestor_'+i+'.fa') + ' could not be opened.'
            print 'Exiting program.'
            sys.exit(1)
        print 'Reading ancestral chromosome '+i+'...'
        f.readline()    ##first >**** line
        ancestor[i]='0'+''.join(line.strip() for line in f)
        f.close()
    return ancestor

def parseances(ancestor, line):
    if line.startswith("#") or line=="\n":
        return ""
    data = line.split('\t')
    chr_num = data[0].split('chr')[-1]
    start = int(data[1])
    return ancestor[chr_num][start:start+len(data[3])].upper()

##list of ancestral alleles for each line in input file,
##"" if metadata line, '.' if none available
ancestors = getAncestors(ancespath)
ancesdata = [parseances(ancestors, line) for line in infile]
del ancestors

#Load exon intervals from .interval file, used later for intersecting with gerp elements
codingExonIntervals = getCodingExonIntervals(options.annotation_interval_path)

## Coordinates are 1-based.
## All GERP intervals include endpoints
GERPratedata=[]
GERPelementdata=[]

GERPrejectiondata = []

infile.seek(0)
line = infile.readline()
while line.startswith("#") or line=="\n":
    GERPratedata.append('')
    GERPelementdata.append('')
    GERPrejectiondata.append('')
    line=infile.readline()

for i in chrs:
    if line.split('\t')[0].split('chr')[-1]!=i:
        print 'no indels on chromosome ' + i
        continue
    #try:
    #    ratefile=open(GERPratepath+'/chr'+i+'.maf.rates')
    #except:
    #    print GERPratepath+'/chr'+i+'.maf.rates could not be opened.'
    #    print 'Exiting program.'
    #    sys.exit(1)
    try:
        elementfile=open(os.path.join(GERPelementpath, 'hg19_chr'+i+'_elems.txt'))
    except:
        print os.path.join(GERPelementpath, 'hg19_chr'+i+'_elems.txt') + ' could not be opened.'
        print 'Exiting program.'
        sys.exit(1)
    print 'Reading GERP information for chromosome '+i+'...'
    #GERPrates=array.array('f',[0])
    #for rateline in ratefile:
    #    GERPrates.append(float(rateline.split('\t')[1]))
    startTime = datetime.datetime.now()
    buildGerpRates(GERPratepath, GERPratecachepath, i)
    
    print str((datetime.datetime.now() - startTime).seconds) + " seconds."
    
    GERPelements = getGERPelements(elementfile)

    print 'Calculating GERP scores for chromosome '+i+'...'
    startTime = datetime.datetime.now()
    while line.split('\t')[0].split('chr')[-1]==i:
        data = line.split('\t')
        chr_num = data[0].split('chr')[-1]
        start = int(data[1])
        length = len(data[3])
        end = start + length-1  ##inclusive endpoint
        #GERPratedata.append(`sum(GERPrates[start:start+length])/length`)
        GERPratedata.append(str(getGerpScore(start, length)))
        ##do binary search to see if contained in any GERP element
        low = 0; high = len(GERPelements)-1
        while low<=high:
            mid = (low+high)/2
            if start>GERPelements[mid][1]:
                low = mid+1
            elif end<GERPelements[mid][0]:
                high = mid-1
            else:
                break
        if low>high:
            GERPelementdata.append(".")
            GERPrejectiondata.append(".")
        else:
            GERPelementdata.append(`GERPelements[mid]`)

            rejectedElements = []
            if 'prematureStop' in line:
                prematureStopIndex = line.index('prematureStop')
                lineComponents = line[prematureStopIndex-2:].split(":")
                direction = lineComponents[0]
                transcript = lineComponents[4]

                rejectedElements = getRejectionElementIntersectionData(codingExonIntervals, GERPelements, mid, chr_num, start, transcript, direction)

            if len(rejectedElements) > 0:
                GERPrejectiondata.append(",".join(["%d/%.2f/%d/%d/%.2f" % rejectedElement for rejectedElement in rejectedElements]))
            else:
                GERPrejectiondata.append(".")
        
        line=infile.readline()
    f.close()
    gerprate.freeMemory()
    print str((datetime.datetime.now() - startTime).seconds) + " seconds."

#del GERPrates
del GERPelements

segdups={}
segdupmax={}
for i in chrs:
    segdups[i] = []
    segdupmax[i] = []
print "Reading segdup information..."
line = segdupfile.readline()
while line.startswith("#") or line=="\n":
    line=segdupfile.readline()
while line!="":
    data = line.split('\t')
    chr_num = data[0].split('chr')[-1]
    if '_' in chr_num:
        line = segdupfile.readline()
        continue
    segdups[chr_num].append((int(data[1]),int(data[2])))
    line = segdupfile.readline()
for i in chrs:
    segdups[i] = sorted(segdups[i])
    maxsofar = 0
    for interval in segdups[i]:
        maxsofar = max(interval[1], maxsofar)
        segdupmax[i].append(maxsofar)
segdupdata=[]
infile.seek(0)
line = infile.readline()
while line.startswith("#") or line=="\n":
    segdupdata.append('')
    line=infile.readline()
print 'Calculating segdup overlaps...'
while line!="":
    data = line.split('\t')
    chr_num = data[0].split('chr')[-1]
    start = int(data[1])
    length = len(data[3])
    end = start + length-1  ##inclusive endpoint

    ##find right endpoint of interval search 
    low = 0; high = len(segdups[chr_num])-1
    while low<=high:
        mid = (low+high)/2
        if end<segdups[chr_num][mid][0]:
            high = mid-1
        elif mid == len(segdups[chr_num])-1 or end<segdups[chr_num][mid+1][0]:
            break
        else:
            low = mid+1
    right = mid
        
    ##find left endpoint of interval search
    low = 0; high = len(segdups[chr_num])-1
    while low<=high:
        mid = (low+high)/2
        if start>segdups[chr_num][mid][1] and start>segdupmax[chr_num][mid]:
            low = mid+1
        elif mid==0:
            break
        elif start>segdups[chr_num][mid-1][1] and start>segdupmax[chr_num][mid-1]:
            break
        else:
            high = mid-1
    left = mid
    
    overlaps = []
    for interval in segdups[chr_num][left:right+1]:
        ##compare bigger of left enpoints to smaller of right endpoints
        if max(start, interval[0]) <= min(end, interval[1]):
            overlaps.append(interval)
    segdupdata.append(`overlaps`)

    line = infile.readline()


## Coordinates for chromosomes are 1-based.
c={}
for i in chrs:
    try:
        f=open(os.path.join(genomepath, 'chr'+i+'.fa'))
    except:
        print os.path.join(genomepath, 'chr'+i+'.fa') + ' could not be opened.'
        print 'Exiting program.'
        sys.exit(1)
    print 'Reading chromosome '+i+'...'
    f.readline()    ##first >chr* line
    c[i]='0'+''.join(line.strip() for line in f)
    f.close()

CDS={}; exon={}; stop_codon={}  ##{chr_num: {transcript: [(a,b),(c,d)..] } }
transcript_strand={}            ##{transcript_id:+ or -}
for chr_num in chrs:
    CDS[chr_num]={}
    exon[chr_num]={}
    stop_codon[chr_num]={}
CDS['M']={}
exon['M']={}
stop_codon['M']={}

## Coordinates for annotation are 1-based and intervals include BOTH endpoints
print 'Building CDS and exon dictionaries...'
startTime = datetime.datetime.now()

##count number of lines preceding actual annotation data
counter = 0
annotfile.seek(0)
for line in annotfile:
    if len(line)<3:
        counter+=1
        continue
    if line.startswith("#"):    ##all preceding lines begin with #
        counter+=1
    else:
        annotfile.seek(0)
        break
for i in range(0,counter):
    annotfile.readline()

##begin going through actual annotation data
oldtr = ""  ##last seen transcript
oldchr = "" ##chr num of last seen transcript
tlines = [] ##all split CDS lines in oldtr
for line in annotfile:
    data = line.strip().split('\t')
    chr_num=data[0].split('chr')[-1]
    annottype = data[2]
    
    if annottype!='exon' and annottype!='transcript' and annottype!='CDS' and annottype!='stop_codon':
        continue
    if annottype=='transcript':
        transcript = data[8].split(';')[1].split('"')[1]
        transcript_strand[transcript]=data[6]
        if oldtr!="":
            if len(tlines)>0:
                if transcript_strand[oldtr]=='+':
                    oldsort = sorted(tlines, key=lambda s: int(s[3]))
                    first = oldsort[0]
                    CDS[oldchr][oldtr].append((int(first[3])+int(first[7]), int(first[4])))
                    for CDSline in oldsort[1:]:
                        CDS[oldchr][oldtr].append((int(CDSline[3]),int(CDSline[4])))
                else:
                    oldsort = sorted(tlines, key=lambda s: int(s[3]), reverse=True)
                    first = oldsort[0]
                    CDS[oldchr][oldtr].append((int(first[3]), int(first[4])-int(first[7])))
                    for CDSline in oldsort[1:]:
                        CDS[oldchr][oldtr].append((int(CDSline[3]),int(CDSline[4])))
        oldtr = transcript
        oldchr = chr_num
        tlines=[]
        exon[chr_num][transcript] = []
        CDS[chr_num][transcript] = []
    else:  ## then is either exon or CDS or stop codon
        begin = int(data[3])
        end = int(data[4])
        if data[2]=='exon':  
            exon[chr_num][transcript].append((begin, end))  ##
        elif data[2]=='CDS':
            tlines.append(data)  ##append data for reanalysis (mRNA_start_NF cases)
        else:  ##stop codon
            stop_codon[chr_num][transcript] = (begin,end)
if len(tlines)>0:
    if transcript_strand[oldtr]=='+':
        oldsort = sorted(tlines, key=lambda s: int(s[3]))
        first = oldsort[0]
        CDS[oldchr][oldtr].append((int(first[3])+int(first[7]), int(first[4])))
        for CDSline in oldsort[1:]:
            CDS[oldchr][oldtr].append((int(CDSline[3]),int(CDSline[4])))
    else:
        oldsort = sorted(tlines, key=lambda s: int(s[3]), reverse=True)
        first = oldsort[0]
        CDS[oldchr][oldtr].append((int(first[3]), int(first[4])-int(first[7])))
        for CDSline in oldsort[1:]:
            CDS[oldchr][oldtr].append((int(CDSline[3]),int(CDSline[4])))

annotfile.close()

print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print 'Begin ALoFT Calculations and Write-Out (this may take a while)...'
def calculateExomeCoordinate(component):
    values = component.split("=")[1].split(",")
    if (int(values[0]) + int(values[1])) == 0:
        return 0.0
    return int(values[0]) * 1.0 / (int(values[0]) + int(values[1]))

#Returns a Pfam vcf-formatted description, and a verbose description
#The vcf-formatted description is in format Pfam_ID:domain_length:max_domain_percent_lost:number_pfams_in_domain:number_pfams_in_truncation
#The verbose description returned is a) a series of concatenated Pfam_ID:domain_length:percent_lost, and a series of concatenated domain_id_lost:domain_length 
def getPfamDescription(transcriptToProteinHash, chromosome, transcriptID, domainValue, chromosomesPFam, domainType):    ##domain value=amino acid coordinate of premature stop
    pfamsMatched = []
    maxPercentageLostPfamIndex = -1
    pfamDescription = ""
    pfamVerboseDescription = None

    chromosomesPFam = chromosomesPFam[domainType]

    if transcriptToProteinHash.has_key(transcriptID) and chromosomesPFam[chromosome].has_key(transcriptToProteinHash[transcriptID]):
        pfamComponentsList = chromosomesPFam[chromosome][transcriptToProteinHash[transcriptID]]
        domainsLost = ""
        numberOfDomainsLost = 0
        for pfamComponents in pfamComponentsList:
            domainComponents = pfamComponents[1].split("-")
            domainStart = int(domainComponents[0])
            domainEnd = int(domainComponents[1])
            domainLength = domainEnd - domainStart + 1
            if domainValue >= domainStart and domainValue <= domainEnd:
                domainLengthLost = domainEnd - domainValue + 1
                domainPercentLost = domainLengthLost * 100.0 / domainLength

                if not pfamVerboseDescription:
                    pfamVerboseDescription = ""

                pfamVerboseDescription += ":%s:%d:%.2f" % (pfamComponents[0], domainLength, domainPercentLost)

                #Find largest percentage lost pfam
                if maxPercentageLostPfamIndex < 0 or domainPercentLost > float(pfamsMatched[maxPercentageLostPfamIndex].split(":")[3]):
                    maxPercentageLostPfamIndex = len(pfamsMatched)

                pfamsMatched.append(":%s:%d:%.2f" % (pfamComponents[0], domainLength, domainPercentLost))

            elif domainValue < domainStart:
                domainsLost += ":" + pfamComponents[0] + ":" + str(domainLength)
                numberOfDomainsLost += 1

        if maxPercentageLostPfamIndex >= 0:
            pfamDescription = pfamsMatched[maxPercentageLostPfamIndex] + ":" + str(len(pfamsMatched))

        if pfamDescription == "":
            pfamDescription = ":NO_"+domainType+":NA:NA:0"
            pfamVerboseDescription = "NO_"+domainType

        verboseDomainsLost = str(domainsLost)
        if verboseDomainsLost.startswith(":"):
            verboseDomainsLost = verboseDomainsLost[1:]

        if verboseDomainsLost == "":
            verboseDomainsLost = "NO_"+domainType

        if pfamVerboseDescription.startswith(":"):
            #Remove beginning colon
            pfamVerboseDescription = pfamVerboseDescription[1:]

        pfamVerboseDescription = [pfamVerboseDescription, verboseDomainsLost]

        #Add number of domains lost
        pfamDescription += ":" + str(numberOfDomainsLost)

    #If no ENST or ENSP ID could be matched
    if pfamDescription == "":
        pfamDescription = ":NO_"+domainType+":NA:NA:0:0"
    if pfamVerboseDescription is None:
        pfamVerboseDescription = ["NO_"+domainType, "NO_"+domainType]

    return pfamDescription, pfamVerboseDescription
        
# Get a mapping of Transcript ID's (ENST) -> Proteins ID's (ENSP)
def getTranscriptToProteinHash(transcriptToProteinFilePath):
    try:
        inputFile = open(transcriptToProteinFilePath, "r")
    except:
        print "Failed to open " + transcriptToProteinFilePath
        sys.exit(1)

    transcriptToProteinHash = {}
    firstLine = True
    for line in inputFile:
        if firstLine:
            firstLine = False
        else:
            components = line.split('\t')
            if components[1].strip() and components[2].strip():
                transcriptToProteinHash[components[1]] = components[2]

    inputFile.close()
    return transcriptToProteinHash

def getChromosomesPfamTable(chrs, pfamDirectory, strformat, domainTypeList, domainTypeColumn=0):
   # Get a mapping of Protein ID's -> Pfam information, for each chromosome
    chromosomesPFam = {i:{} for i in domainTypeList}
    for chromosome in chrs:
        for domainType in domainTypeList:
            chromosomesPFam[domainType][chromosome] = {}
        path = os.path.join(pfamDirectory, strformat % (chromosome))

        #Get rid of duplicate lines
        try:
            pipe1 = Popen(['sort', path], stdout=PIPE)
            pipe2 = Popen(['uniq'], stdin=pipe1.stdout, stdout=PIPE)
            inputFile = pipe2.stdout
        except:
            print "Couldn't read " + path + " , skipping chr" + chromosome
            continue

        linesToSkip = 2
        for line in inputFile:
            if linesToSkip > 0:
                linesToSkip -= 1
            else:
                components = line.split("\t")
                digitmatch = re.search("\d", components[domainTypeColumn])
                if not digitmatch:
                    domainType = components[domainTypeColumn].strip()
                else:
                    domainType = components[domainTypeColumn][:digitmatch.start()]
                if domainType not in domainTypeList:
                    continue
                if len(components) >= 3:
                    translationID = components[2].replace('(', '').replace(')', '').strip()
                    if chromosomesPFam[domainType][chromosome].has_key(translationID):
                        chromosomesPFam[domainType][chromosome][translationID].append(components)
                    else:
                        chromosomesPFam[domainType][chromosome][translationID] = [components]

        inputFile.close()

    return chromosomesPFam
        
transcriptToProteinHash = getTranscriptToProteinHash(transcriptToProteinFilePath)

##{'1':{'ENSP...':'PF...\t4-25\t(ENSP...)'}, '2':{...}, ...}
chromosomesPFam = dict(getChromosomesPfamTable(chrs, proteinfeaturesDirectory, r"chr%s.prot-features-ens70.txt", ["PF", "SSF", "SM"]).items() + getChromosomesPfamTable(chrs, phosphorylationDirectory, r"ptm.phosphosite.chr%s.txt", ["ACETYLATION", "DI-METHYLATION", "METHYLATION", "MONO-METHYLATION", "O-GlcNAc", "PHOSPHORYLATION", "SUMOYLATION", "TRI-METHYLATION", "UBIQUITINATION"], 3).items() + getChromosomesPfamTable(chrs, transmembraneDirectory, r"chr%s.tmsigpcoilslc.ens70.txt", ["Tmhmm", "Sigp"]).items())

exomesChromsomeInfo = {}

#Scan 1000G file
print "Scanning 1000G file"
startTime = datetime.datetime.now()

thousandGChromosomeInfo = {}

for thousandGLine in thousandGInputFile:
    if not thousandGLine.startswith("#"):
        thousandGLineComponents = thousandGLine.rstrip("\n").split("\t")
        thousandGChromosomeNumber = thousandGLineComponents[0].replace("chr", "")
        if not thousandGChromosomeInfo.has_key(thousandGChromosomeNumber):
            thousandGChromosomeInfo[thousandGChromosomeNumber] = {}
        
        thousandGChromosomeInfo[thousandGChromosomeNumber][int(thousandGLineComponents[1])] = thousandGLineComponents[7]

thousandGInputFile.close()

print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading ppi network"
#startTime = datetime.datetime.now()

#Read ppi network
ppi = nx.Graph()
ppifile.readline()
for line in ppifile:
    data = line.split('\t')
    ppi.add_edge(data[2], data[3])
ppifile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading recessive genes list"
#startTime = datetime.datetime.now()

#Read recessive genes list
rgenes = []
for line in rgenesfile:
    rgenes.append(line.strip())
rgenesfile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading dominant genes list"
#startTime = datetime.datetime.now()

#Read dominant genes list
dgenes = []
for line in dgenesfile:
    dgenes.append(line.strip())
dgenesfile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading haploinsufficiency disease genes list"
#startTime = datetime.datetime.now()

#Read haploinsufficiency disease scores
haploscores = {}
haploscorefile.readline()
for line in haploscorefile:
    data = line.strip().split('\t')
    haploscores[data[0].upper()] = data[1]
haploscorefile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading LOF disease scores"
#startTime = datetime.datetime.now()

#Read LOF disease scores
LOFscores = {}
LOFscorefile.readline()
for line in LOFscorefile:
    data = line.strip().split('\t')
    LOFscores[data[0].upper()] = data[1]
LOFscorefile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading netSNP disease scores"
#startTime = datetime.datetime.now()

#Read netSNP disease scores
netSNPscores = {}
netSNPscorefile.readline()
for line in netSNPscorefile:
    data = line.strip().split('\t')
    netSNPscores[data[0].upper()] = data[-1]
netSNPscorefile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading pseudogene data"
#startTime = datetime.datetime.now()

#Read pseudogene data
numpseudogenes = {}     ##{parent transcript: # of assoc. pseudogenes}
pseudogenesfile.readline()
for line in pseudogenesfile:
    tx = line.split('\t')[6]
    if tx in numpseudogenes:
        numpseudogenes[tx] = numpseudogenes[tx]+1
    else:
        numpseudogenes[tx] = 1
pseudogenesfile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading paralog data"
#startTime = datetime.datetime.now()

#Read paralog data
paralogs = {}     ##{ENSG ID (without . subclassifier): set(assoc. paralogs)}
paralogsfile.readline()
for line in paralogsfile:
    id1 = line.split('\t')[0]
    id2 = line.split('\t')[1]
    if id1 not in paralogs:
        paralogs[id1] = set()
    paralogs[id1].add(id2)
    if id2 not in paralogs:
        paralogs[id2] = set()
    paralogs[id2].add(id1)
paralogsfile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

print "Reading dNdS data"
#startTime = datetime.datetime.now()

#Read dNdS data
dNdSmacaque = {}      ##{ENST ID (without . subclassifier): dN/dS (STRING)}
dNdSmouse = {}
dNdSfile.readline()
for line in dNdSfile:
    data = line.strip().split('\t')
    tx = data[1]
    dNdSmacaque[tx] = data[2]
    dNdSmouse[tx] = data[3]
dNdSfile.close()

#print str((datetime.datetime.now() - startTime).seconds) + " seconds."

##list of output parameters for LOF and splice variants
basicparams = ["gene", "gene_id", "partial/full", "transcript",\
                "transcript length", "longest transcript?"]
LOFparams = ["shortest path to recessive gene", "recessive neighbors",\
                "shortest path to dominant gene", "dominant neighbors",\
                "is single coding exon?",\
                "indel position in CDS", "stop position in CDS",\
                "causes NMD?", "5' flanking splice site",\
                "3' flanking splice site", "canonical?",\
                "# failed filters", "filters failed",\
                "ancestral allele", "GERP score", "GERP element", "GERP rejection", "Disorder prediction",\
                "segmental duplications", "PFAM", "PFAMtruncated",\
                "SCOP", "SCOPtruncated", "SM", "SMtruncated",\
                "Tmhmm", "Tmhmmtruncated", "Sigp", "Sigptruncated",\
                "ACETYLATION", "ACETYLATIONtruncated", "DI-METHYLATION", "DI-METHYLATIONtruncated",\
                "METHYLATION", "METHYLATIONtruncated", "MONO-METHYLATION", "MONO-METHYLATIONtruncated",\
                "O-GlcNAc", "O-GlcNActruncated","PHOSPHORYLATION", "PHOSPHORYLATIONtruncated", "SUMOYLATION", "SUMOYLATIONtruncated",\
                "TRI-METHYLATION", "TRI-METHYLATIONtruncated", "UBIQUITINATION", "UBIQUITINATIONtruncated",\
                "1000GPhase1", "1000GPhase1_AF", "1000GPhase1_ASN_AF",\
                "1000GPhase1_AFR_AF", "1000GPhase1_EUR_AF",\
                "ESP6500", "ESP6500_AAF",\
                "haploinsufficiency disease score",\
                "LOF disease score", "netSNP disease score",\
                "# pseudogenes associated to transcript",\
                "# paralogs associated to gene",\
                "dN/dS (macaque)", "dN/dS (mouse)"]
spliceparams = ["shortest path to recessive gene", "recessive neighbors",\
                "shortest path to dominant gene", "dominant neighbors",\
                "donor", "acceptor",\
                "SNP in canonical site?", "other splice site canonical?",\
                "SNP location", "alt donor", "alt acceptor",\
                "intron length", "# failed filters", "filters failed",\
                "GERP score", "GERP element", "GERP rejection", "Disorder prediction",\
                "segmental duplications", "PFAM", "PFAMtruncated",\
                "SCOP", "SCOPtruncated", "SM", "SMtruncated",\
                "Tmhmm", "Tmhmmtruncated", "Sigp", "Sigptruncated",\
                "ACETYLATION", "ACETYLATIONtruncated", "DI-METHYLATION", "DI-METHYLATIONtruncated",\
                "METHYLATION", "METHYLATIONtruncated", "MONO-METHYLATION", "MONO-METHYLATIONtruncated",\
                "O-GlcNAc", "O-GlcNActruncated","PHOSPHORYLATION", "PHOSPHORYLATIONtruncated", "SUMOYLATION", "SUMOYLATIONtruncated",\
                "TRI-METHYLATION", "TRI-METHYLATIONtruncated", "UBIQUITINATION", "UBIQUITINATIONtruncated",\
                "1000GPhase1", "1000GPhase1_AF", "1000GPhase1_ASN_AF",\
                "1000GPhase1_AFR_AF", "1000GPhase1_EUR_AF",\
                "ESP6500", "ESP6500_AAF",\
                "haploinsufficiency disease score",\
                "LOF disease score", "netSNP disease score",\
                "# pseudogenes associated to transcript",\
                "# paralogs associated to gene",\
                "dN/dS (macaque)", "dN/dS (mouse)"]
outdata = {i : "" for i in set(basicparams) | set(LOFparams) | set(spliceparams)}

o_lof.write('chr\tpos\trsID\tref\talt\tscore\tPASS?\tdetails\t')
o_lof.write('\t'.join(i for i in basicparams)+'\t')
o_lof.write('\t'.join(i for i in LOFparams)+'\n')

o_splice.write('chr\tpos\trsID\tref\talt\tscore\tPASS?\tdetails\t')
o_splice.write('\t'.join(i for i in basicparams)+'\t')
o_splice.write('\t'.join(i for i in spliceparams)+'\n')

##scan through VCF file metadata
counter = 0
infile.seek(0)
line = infile.readline()
while line=="\n" or line.startswith("#"):
    o2.write(line)
    counter+=1
    line = infile.readline()

while line!="":
    data = line.strip().split('\t')
    chr_num = data[0].split("chr")[-1]
    start = int(data[1])
    end = start+len(data[3])-1
    
    #Filter lines
    if "deletionFS" in line or "insertionFS" in line or "premature" in line or "splice" in line:
        if data[3] == ancesdata[counter]:
            ancestral = "Ref"
        elif data[4] == ancesdata[counter]:
            ancestral = "Alt"
        else:
            ancestral = "Neither"

        disopredData = getDisopredDataFromLine(disopredSequencesPath, line)
        
        ##screen for variant types here.  skip variant if it is not deletion(N)FS, insertion(N)FS, or premature SNP
        lineinfo = {'AA':'AA='+ancesdata[counter],\
                    'Ancestral':'Ancestral='+ancestral,\
                    'GERPscore':'GERPscore='+GERPratedata[counter],\
                    'GERPelement':'GERPelement='+GERPelementdata[counter],\
                    'GERPrejection':'GERPrejection='+GERPrejectiondata[counter],\
                    'Disorderprediction':'Disorderprediction='+disopredData,\
                    'SegDup':'SegDup='+`segdupdata[counter].count('(')`}
        infotypes = ['AA', 'Ancestral', 'GERPscore', 'GERPelement', 'GERPrejection', 'Disorderprediction', 'SegDup']

        outdata["ancestral allele"] = ancesdata[counter]
        outdata["GERP score"] = GERPratedata[counter]
        outdata["GERP element"] = GERPelementdata[counter]
        outdata["GERP rejection"] = GERPrejectiondata[counter]
        outdata["Disorder prediction"] = disopredData
        outdata["segmental duplications"] = '.' if segdupdata[counter].count('(') == '0' else segdupdata[counter]
        outdata["PFAM"] = "N/A"
        outdata["PFAMtruncated"] = "N/A"
        outdata["SCOP"] = "N/A"
        outdata["SCOPtruncated"] = "N/A"
        outdata["SM"] = "N/A"
        outdata["SMtruncated"] = "N/A"
        outdata["Tmhmm"] = "N/A"
        outdata["Tmhmmtruncated"] = "N/A"
        outdata["Sigp"] = "N/A"
        outdata["Sigptruncated"] = "N/A"
        outdata["ACETYLATION"] = "N/A"
        outdata["ACETYLATIONtruncated"] = "N/A"
        outdata["DI_METHYLATION"] = "N/A"
        outdata["DI_METHYLATIONtruncated"] = "N/A"
        outdata['METHYLATION'] = "N/A"
        outdata['METHYLATIONtruncated']
        outdata['MONO-METHYLATION'] = "N/A"
        outdata['MONO-METHYLATIONtruncated'] = "N/A"
        outdata['O-GlcNAc'] = "N/A"
        outdata['O-GlcNActruncated'] = "N/A"
        outdata['PHOSPHORYLATION'] = "N/A"
        outdata['PHOSPHORYLATIONtruncated'] = "N/A"
        outdata['SUMOYLATION'] = "N/A"
        outdata['SUMOYLATIONtruncated'] = "N/A"
        outdata['TRI-METHYLATION'] = "N/A"
        outdata['TRI-METHYLATIONtruncated'] = "N/A"
        outdata['UBIQUITINATION'] = "N/A"
        outdata['UBIQUITINATIONtruncated'] = "N/A"

        #Adding 1000G fields
        thousandGTags = ['1000GPhase1_AF', '1000GPhase1_ASN_AF', '1000GPhase1_AFR_AF', '1000GPhase1_EUR_AF']
        thousandGComponents = []
        for thousandGTag in thousandGTags:
            thousandGComponents.append(thousandGTag + "=NA")
        
        if thousandGChromosomeInfo.has_key(chr_num) and thousandGChromosomeInfo[chr_num].has_key(start):
            for info in thousandGChromosomeInfo[chr_num][start].split(";"):
                infotype = info.split('=')[0]
                
                newComponent = "1000GPhase1_" + info
                thousandGComponentIndex = -1
                for findIndex in xrange(len(thousandGTags)):
                    if infotype == "_".join(thousandGTags[findIndex].split("_")[1:]):
                        thousandGComponentIndex = findIndex
                        break
                
                if thousandGComponentIndex >= 0:
                    thousandGComponents[thousandGComponentIndex] = newComponent
        
        infotypes += ['1000GPhase1'] + thousandGTags
        if thousandGChromosomeInfo.has_key(chr_num) and thousandGChromosomeInfo[chr_num].has_key(start):
            lineinfo['1000GPhase1'] = '1000GPhase1=Yes'
        else:
            lineinfo['1000GPhase1'] = '1000GPhase1=No'
        
        #Add 1000G entries to output
        for tagIndex in xrange(len(thousandGTags)):
            lineinfo[thousandGTags[tagIndex]] = thousandGComponents[tagIndex]
        
        #Adding ESP6500 (exome) fields
        if not exomesChromsomeInfo.has_key(chr_num):
            exomesChromsomeInfo = {chr_num : {}}
            exomePath = os.path.join(exomeDirectory, 'ESP6500.chr%s.snps.vcf' % (chr_num)) 
            try:
                exomeInputFile = open(exomePath, "r")
            except:
                print "Couldn't read " + exomePath
                print "Skipping..."
                exomeInputFile = None
            
            if exomeInputFile:
                for exomeLine in exomeInputFile:
                    if not exomeLine.startswith("#"):
                        exomeLineComponents = exomeLine.split("\t")
                        
                        x = "NA"
                        y = "NA"
                        z = "NA"
                        for component in exomeLineComponents[7].split(";"):
                            if component.startswith('EA_AC='):
                                x = "%.4f" % (calculateExomeCoordinate(component))
                            elif component.startswith('AA_AC='):
                                y = "%.4f" % (calculateExomeCoordinate(component))
                            elif component.startswith('TAC='):
                                z = "%.4f" % (calculateExomeCoordinate(component))
                                
                        exomesChromsomeInfo[chr_num][int(exomeLineComponents[1])] = ("%s,%s,%s" % (x, y, z))
                
                exomeInputFile.close()
        
        #Add exomes info to output
        infotypes += ['ESP6500', 'ESP6500_AAF']
        if exomesChromsomeInfo[chr_num].has_key(start):
            lineinfo['ESP6500'] = 'ESP6500=Yes'
            lineinfo['ESP6500_AAF'] = 'ESP6500_AAF=' + exomesChromsomeInfo[chr_num][start]
        else:
            lineinfo['ESP6500'] = 'ESP6500=No'
            lineinfo['ESP6500_AAF'] = 'ESP6500_AAF=NA,NA,NA'

        for tag in ['1000GPhase1'] + thousandGTags + ['ESP6500', 'ESP6500_AAF']:
            outdata[tag] = lineinfo[tag]
        
        dataInfoComponents = data[7].split(';')
        found = 0
        for info in dataInfoComponents:
            infotype = info.split('=')[0]
            if infotype == 'VA':
                variants = info.split('VA=')[-1].split(',')
                found = 1
            if infotype!='AA' and infotype!='VA':
                lineinfo[infotype]=info
                infotypes.append(infotype)
        
        if found==1:
            lineinfo['VA']='VA='
            infotypes.append('VA')
        
        LOFvariants = []
        splicevariants = []
        othervariants = []
        for variant in variants:
            ##alternate allele corresponding to variant
            subst = data[4].split(',')[int(variant.split(':')[0])-1]
            
            if "deletionFS" not in variant and "insertionFS" not in variant:
                if "premature" not in variant and "splice" not in variant:
                    othervariants.append(variant)
                    continue
            details = variant.split(":")

            outdata["gene"], outdata["gene_id"] = details[1], details[2]

            if details[5].split("/")[0]==details[5].split("/")[1]:
                pf = "full"
            else:
                pf = "partial"
            outdata["partial/full"] = pf
            
            transcripts = []

            for i in range(6, len(details)-1, 3):
                transcripts.append(details[i:i+3])
            longesttranscript = max([int(i[2].split('_')[0]) for i in transcripts])

            ##calculate distance to recessive genes
            gene_name = outdata["gene"]

            if False and gene_name in ppi:
                #startTime = datetime.datetime.now()

                dominantdist = 0
                for i in dgenes:
                    if i!=gene_name and i in ppi and nx.has_path(ppi, gene_name, i):
                        if dominantdist==0:
                            dominantdist = nx.shortest_path_length(ppi, gene_name, i)
                        else:
                            dominantdist = min(dominantdist, nx.shortest_path_length(ppi, gene_name, i))
                if dominantdist == 0: ##gene_name is contained in a minor component of the PPI
                    dominantdist = 'N/A'
                outdata["shortest path to dominant gene"] = str(dominantdist)
                numberOfDominantNeighbors = sum(1 for i in dgenes if i in ppi.neighbors(gene_name))
                outdata["dominant neighbors"] = str(numberOfDominantNeighbors)

                recessdist = 0
                for i in rgenes:
                    if  i!=gene_name and i in ppi and nx.has_path(ppi, gene_name, i):
                        if recessdist==0:
                            recessdist = nx.shortest_path_length(ppi, gene_name, i)
                        else:
                            recessdist = min(recessdist, nx.shortest_path_length(ppi, gene_name, i))
                if recessdist == 0: ##gene_name is contained in a minor component of the PPI
                    recessdist = 'N/A'
                outdata["shortest path to recessive gene"] = str(recessdist)
                numberOfRecessiveNeighbors = sum(1 for i in rgenes if i in ppi.neighbors(gene_name))
                outdata["recessive neighbors"] = str(numberOfRecessiveNeighbors)

                #print str((datetime.datetime.now() - startTime).microseconds / 1000000.0) + " ppi seconds."
            else:
                outdata["shortest path to recessive gene"] = 'N/A'
                outdata["recessive neighbors"] = 'N/A'

                outdata["shortest path to dominant gene"] = 'N/A'
                outdata["dominant neighbors"] = 'N/A'

            outdata["haploinsufficiency disease score"] = haploscores[gene_name.upper()] if gene_name.upper() in haploscores else "N/A"
            outdata["LOF disease score"] = LOFscores[gene_name.upper()] if gene_name.upper() in LOFscores else "N/A"
            outdata["netSNP disease score"] = netSNPscores[gene_name.upper()] if gene_name.upper() in netSNPscores else "N/A"
            outdata["# paralogs associated to gene"] = `len(paralogs[outdata["gene_id"].split('.')[0]])` if outdata["gene_id"].split('.')[0] in paralogs else "0"

            ##number of associated pseudogenes computation goes here

            if "splice" in variant:
                ##check that is a SNP splice variant
                if len(data[3])>1 or len(subst)>1:
                    splicevariants.append(variant)
                    continue
                splicevariants.append(':'.join(details[:6]))

                for entry in transcripts:
                    splicevariants[-1]+=':' + ':'.join(entry[0:1] + [pf] + entry[1:])
                    transcript = entry[1]
                    outdata["transcript"] = transcript
                    outdata["transcript length"] = entry[2]
                    outdata["longest transcript?"] = "YES" if int(outdata["transcript length"])==longesttranscript else "NO"
                    ispositivestr = transcript_strand[transcript]=='+'

                    outdata["# pseudogenes associated to transcript"] = `numpseudogenes[transcript]` if transcript in numpseudogenes else "0"
                    outdata["dN/dS (macaque)"] = dNdSmacaque[transcript.split('.')[0]] if transcript.split('.')[0] in dNdSmacaque else "N/A"
                    outdata["dN/dS (mouse)"] = dNdSmouse[transcript.split('.')[0]] if transcript.split('.')[0] in dNdSmouse else "N/A"
                    
                    #Insert Ancestral after AA=
                    tabOutputLineStripped = line.strip()
                    ancestralInsertionIndex = tabOutputLineStripped.find(';', tabOutputLineStripped.find('AA='))
##########################################################
                    o_splice.write(tabOutputLineStripped[0:ancestralInsertionIndex] + ';' + lineinfo['Ancestral'] + tabOutputLineStripped[ancestralInsertionIndex:])
                    o_splice.write('\t'+ '\t'.join(outdata[i] for i in basicparams))
#########################################################

                    l = sorted(CDS[chr_num][transcript], reverse= not ispositivestr)
                    found = 0
                    end = 0  ##0 for end toward smaller basepair number, 1 for other end
                    for i in range(0,len(l)):
                        r = l[i]
                        if start-r[1] in [1,2]:
                            end = 1
                            found = 1
                            break
                        elif r[0]-start in [1,2]:
                            end = 0
                            found = 1
                            break
#########################################################
                    if not found:
                        o_splice.write('\t'+'\t'.join(outdata[i] for i in ["shortest path to recessive gene", "recessive neighbors"]))
                        o_splice.write("\tCDS match not found: pos="+`start`+' transcript='+transcript+'\n')
                        continue
                    if ispositivestr:
                        if (end==0 and i==0) or (end==1 and i==len(l)-1):
                            o_splice.write('\t'+'\t'.join(outdata[i] for i in ["shortest path to recessive gene", "recessive neighbors"]))
                            o_splice.write("\tno donor/acceptor pair: pos="+`start`+' transcript='+transcript+'\n')
#########################################################
                            continue
                        if end==0:
                            acceptor = c[chr_num][l[i][0]-2:l[i][0]].upper()
                            if start==l[i][0]-2:
                                new = (1, subst+acceptor[1])
                            else:
                                new = (1, acceptor[0]+subst)
                            donor = c[chr_num][l[i-1][1]+1:l[i-1][1]+3].upper()
                            intronlength = l[i][0]-l[i-1][1]-1
                        elif end==1:
                            acceptor = c[chr_num][l[i+1][0]-2:l[i+1][0]].upper()
                            donor = c[chr_num][l[i][1]+1:l[i][1]+3].upper()
                            if start==l[i][1]+1:
                                new = (0, subst+donor[1])
                            else:
                                new = (0, donor[0]+subst)
                            intronlength = l[i+1][0]-l[i][1]-1
                    else:   ##not ispositivestr
                        if (end==1 and i==0) or (end==0 and i==len(l)-1):
#########################################################
                            o_splice.write('\t'+'\t'.join(outdata[i] for i in ["shortest path to recessive gene", "recessive neighbors"]))
                            o_splice.write("\tno donor/acceptor pair: pos="+`start`+' transcript='+transcript+'\n')
#########################################################
                            continue
                        if end==0:
                            donor = c[chr_num][l[i][0]-2:l[i][0]].upper()
                            acceptor = c[chr_num][l[i+1][1]+1:l[i+1][1]+3].upper()
                            if start==l[i][0]-2:
                                new = (0, subst+donor[1])
                            else:
                                new = (0, donor[0]+subst)
                            intronlength = l[i][0]-l[i+1][1]-1
                        elif end==1:
                            donor = c[chr_num][l[i-1][0]-2:l[i-1][0]].upper()
                            acceptor = c[chr_num][l[i][1]+1:l[i][1]+3].upper()
                            if start==l[i][1]+1:
                                new = (1, subst+acceptor[1])
                            else:
                                new = (1, acceptor[0]+subst)
                            intronlength = l[i-1][0]-l[i][1]-1
                        donor = compstr(donor.upper())
                        acceptor = compstr(acceptor.upper())
                        new = (new[0],compstr(new[1].upper()))
                    outdata["donor"] = donor
                    outdata["acceptor"] = acceptor
                    outdata["intron length"] = `intronlength`
                    ##write to output
                    if new[0]==0:
                        isCanonical = 'YES' if donor=='GT' else 'NO'
                        otherCanonical = 'YES' if acceptor=='AG' else 'NO'
                    elif new[0]==1:
                        isCanonical = 'YES' if acceptor=='AG' else 'NO'
                        otherCanonical = 'YES' if donor=='GT' else 'NO'
                    outdata["SNP in canonical site?"] = isCanonical
                    outdata["other splice site canonical?"] = otherCanonical
                    
                    if new[0]==0:
                        outdata["SNP location"] = "donor"
                        outdata["alt donor"] = new[1].upper()
                        outdata["alt acceptor"] = acceptor

                    else:
                        outdata["SNP location"] = "acceptor"
                        outdata["alt donor"] = donor
                        outdata["alt acceptor"] = new[1].upper()

		    #calculation of filters
                    filters_failed = 0
                    failed_filters = []
                    if isCanonical == 'NO':
                        filters_failed = filters_failed+1
                        failed_filters.append('noncanonical')
                    if otherCanonical == 'NO':
                        filters_failed = filters_failed+1
                        failed_filters.append('other_noncanonical')
                    if intronlength < 15:
                        filters_failed = filters_failed+1
                        failed_filters.append('short_intron')
                    if segdupdata[counter].count('(') > 3:
                        filters_failed = filters_failed+1
                        failed_filters.append('heavily_duplicated')

                    outdata["# failed filters"] = `filters_failed`
                    outdata["filters failed"] = ','.join(failed_filters)
					
########################################################
                    o_splice.write("\t"+"\t".join(outdata[i] for i in spliceparams)+"\n")
#########################################################
                    splicevariants[-1]+=':'+':'.join([donor+'/'+acceptor,\
                                                      isCanonical, otherCanonical,\
                                                      `intronlength`])
                    
            else:   ##deletionFS, insertionFS, or prematureStop
                LOFvariants.append(':'.join(details[:6]))

                for entry in transcripts:
                    LOFvariants[-1]+=':'+':'.join(entry[0:1] + [pf] + entry[1:])
                    
                    tlength = entry[2].split('_')[0]
                    outdata["transcript length"] = tlength
                    try:
                        LOFposition = entry[2].split('_')[1]
                    except:
                        LOFposition = '.'
                    outdata["longest transcript?"] = "YES" if int(tlength)==longesttranscript else "NO"
                    transcript = entry[1]
                    outdata["transcript"]=transcript
                   
		    #calculation of filters
                    filters_failed = 0
                    failed_filters = []
                    try:	#since LOFposition may not be provided
                        if float(LOFposition)/float(tlength) <= 0.05:
                            filters_failed = filters_failed+1
                            failed_filters.append('near_start')
                        if float(LOFposition)/float(tlength) >= 0.95:
                            filters_failed = filters_failed+1
                            failed_filters.append('near_stop')
                    except:
                        pass
                    if ancesdata[counter]==subst:
                        filters_failed = filters_failed+1
                        failed_filters.append('lof_anc')
                    if segdupdata[counter].count('(') > 3:
                        filters_failed = filters_failed+1
                        failed_filters.append('heavily_duplicated')
                    outdata["# failed filters"] = `filters_failed`
                    outdata["filters failed"] = ','.join(failed_filters)
 
                    if "prematureStop" in variant:
                        pfamDescription, pfamTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "PF")
                        SCOPDescription, SCOPTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "SSF")
                        SMDescription, SMTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "SM")
                        TmhmmDescription, TmhmmTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "Tmhmm")
                        SigpDescription, SigpTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "Sigp")
                        ACETYLATIONDescription, ACETYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "ACETYLATION")

                        DI_METHYLATIONDescription, DI_METHYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "DI-METHYLATION")
                        METHYLATIONDescription, METHYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "METHYLATION")
                        MONO_METHYLATIONDescription, MONO_METHYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "MONO-METHYLATION")
                        O_GlcNAcDescription, O_GlcNAcTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "O-GlcNAc")
                        PHOSPHORYLATIONDescription, PHOSPHORYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "PHOSPHORYLATION")
                        SUMOYLATIONDescription, SUMOYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "SUMOYLATION")
                        TRI_METHYLATIONDescription, TRI_METHYLATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "TRI-METHYLATION")
                        UBIQUITINATIONDescription, UBIQUITINATIONTabbedDescription = getPfamDescription(transcriptToProteinHash, chr_num, transcript.split(".")[0], int(entry[2].split('_')[2]), chromosomesPFam, "UBIQUITINATION")
                    else:
                        pfamDescription, pfamTabbedDescription = '', ['N/A', 'N/A']
                        SCOPDescription, SCOPTabbedDescription = '', ['N/A', 'N/A']
                        SMDescription, SMTabbedDescription = '', ['N/A', 'N/A']
                        TmhmmDescription, TmhmmTabbedDescription = '', ['N/A', 'N/A']
                        SigpDescription, SigpTabbedDescription = '', ['N/A', 'N/A']
                        ACETYLATIONDescription, ACETYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        DI_METHYLATIONDescription, DI_METHYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        METHYLATIONDescription, METHYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        MONO_METHYLATIONDescription, MONO_METHYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        O_GlcNAcDescription, O_GlcNAcTabbedDescription = '', ['N/A', 'N/A']
                        PHOSPHORYLATIONDescription, PHOSPHORYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        SUMOYLATIONDescription, SUMOYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        TRI_METHYLATIONDescription, TRI_METHYLATIONTabbedDescription = '', ['N/A', 'N/A']
                        UBIQUITINATIONDescription, UBIQUITINATIONTabbedDescription = '', ['N/A', 'N/A']

                    outdata["PFAM"] = pfamTabbedDescription[0]
                    outdata["PFAMtruncated"] = pfamTabbedDescription[1]
                    outdata["SCOP"] = SCOPTabbedDescription[0]
                    outdata["SCOPtruncated"] = SCOPTabbedDescription[1]
                    outdata["SM"] = SMTabbedDescription[0]
                    outdata["SMtruncated"] = SMTabbedDescription[1]
                    outdata["Tmhmm"] = TmhmmTabbedDescription[0]
                    outdata["Tmhmmtruncated"] = TmhmmTabbedDescription[1]
                    outdata["Sigp"] = SigpTabbedDescription[0]
                    outdata["Sigptruncated"] = SigpTabbedDescription[1]
                    outdata["ACETYLATION"] = ACETYLATIONTabbedDescription[0]
                    outdata["ACETYLATIONtruncated"] = ACETYLATIONTabbedDescription[1]
                    outdata["DI-METHYLATION"] = DI_METHYLATIONTabbedDescription[0]
                    outdata["DI-METHYLATIONtruncated"] = DI_METHYLATIONTabbedDescription[1]
                    outdata["METHYLATION"] = METHYLATIONTabbedDescription[0]
                    outdata["METHYLATIONtruncated"] = METHYLATIONTabbedDescription[1]
                    outdata["MONO-METHYLATION"] = MONO_METHYLATIONTabbedDescription[0]
                    outdata["MONO-METHYLATIONtruncated"] = MONO_METHYLATIONTabbedDescription[1]
                    outdata["O-GlcNAc"] = O_GlcNAcTabbedDescription[0]
                    outdata["O-GlcNActruncated"] = O_GlcNAcTabbedDescription[1]
                    outdata["PHOSPHORYLATION"] = PHOSPHORYLATIONTabbedDescription[0]
                    outdata["PHOSPHORYLATIONtruncated"] = PHOSPHORYLATIONTabbedDescription[1]
                    outdata["SUMOYLATION"] = SUMOYLATIONTabbedDescription[0]
                    outdata["SUMOYLATIONtruncated"] = SUMOYLATIONTabbedDescription[1]
                    outdata["TRI-METHYLATION"] = TRI_METHYLATIONTabbedDescription[0]
                    outdata["TRI-METHYLATIONtruncated"] = TRI_METHYLATIONTabbedDescription[1]
                    outdata["UBIQUITINATION"] = UBIQUITINATIONTabbedDescription[0]
                    outdata["UBIQUITINATIONtruncated"] = UBIQUITINATIONTabbedDescription[1]

                    outdata["indel position in CDS"] = "N/A"
                    outdata["stop position in CDS"] = "N/A"
                    outdata["5' flanking splice site"] = "N/A"
                    outdata["3' flanking splice site"] = "N/A"
                    outdata["canonical?"] = "N/A"
                    outdata["# pseudogenes associated to transcript"] = `numpseudogenes[transcript]` if transcript in numpseudogenes else "0"
                    outdata["dN/dS (macaque)"] = dNdSmacaque[transcript.split('.')[0]] if transcript.split('.')[0] in dNdSmacaque else "N/A"
                    outdata["dN/dS (mouse)"] = dNdSmouse[transcript.split('.')[0]] if transcript.split('.')[0] in dNdSmouse else "N/A"
                        
                    #Insert Ancestral after AA=
                    tabOutputLineStripped = line.strip()
                    ancestralInsertionIndex = tabOutputLineStripped.find(';', tabOutputLineStripped.find('AA='))
#########################################################
                    o_lof.write(tabOutputLineStripped[0:ancestralInsertionIndex] + ';' + lineinfo['Ancestral'] + tabOutputLineStripped[ancestralInsertionIndex:])
                    o_lof.write('\t'+'\t'.join(outdata[i] for i in basicparams))
#########################################################
                    
                    l = sorted(CDS[chr_num][transcript])
                    if len(l)==0:
                        continue
                    outdata["is single coding exon?"] = "YES" if len(l)==1 else "NO"
                    m = sorted(exon[chr_num][transcript])   ## m is number of exons
                    CDSseq = ''; exonseq = ''
                    CDSprec = []; exonprec = []             ## prec holds # preceding nucleotides
                    ispositivestr = transcript_strand[transcript]=='+'

                    ## build spliced exon and CDS sequences and maintain coordinate wrt transcript
                    tot = 0
                    for j in range(0,len(l)):
                        if ispositivestr:
                            i=j
                            CDSseq+=c[chr_num][l[i][0]:l[i][1]+1].upper()
                        else:
                            i=len(l)-j-1
                            CDSseq+=compstr(c[chr_num][l[i][0]:l[i][1]+1].upper())
                        CDSprec.append(tot)              ## stores in index i
                        tot += l[i][1]+1-l[i][0]
                    ## add on STOP sequence if annotated
                    try:
                        s = stop_codon[chr_num][transcript]
                    except:
                        s=(2,0)
                    if ispositivestr:
                        CDSseq+=c[chr_num][s[0]:s[1]+1].upper()
                    else:
                        CDSseq+=compstr(c[chr_num][s[0]:s[1]+1].upper())
                    
                    tot = 0
                    for j in range(0,len(m)):
                        if ispositivestr:
                            i=j
                            exonseq+=c[chr_num][m[i][0]:m[i][1]+1].upper()
                        else:
                            i=len(m)-j-1
                            exonseq+=compstr(c[chr_num][m[i][0]:m[i][1]+1].upper())
                        exonprec.append(tot)            ## stores in index i
                        tot += m[i][1]+1-m[i][0]

                    ##build coding exons IN ORDER OF TRANSLATION, i.e. start->stop
                    coding_exons = []           ## flag coding exons (corresponds to exonpos)
                    CDS2ex = {}                 ## maps CDSpos to exonpos    
                    for i in range(0,len(m)):   ## i = exonpos
                        k = i if ispositivestr else len(m)-i-1  ## k = exonindex
                        coding_exons.append(0)
                        for j in range(0,len(l)):   ## j = CDSindex
                            if l[j][0]>=m[k][0] and l[j][1]<=m[k][1]:
                                coding_exons[i] = 1
                                j2 = j if ispositivestr else len(l)-j-1     ## j2 = CDSpos
                                CDS2ex[j2]=i
                                break
                                
                    ncodingexons = sum(coding_exons)    ## number of coding exons
                    try:
                        UTR=len(m)-(coding_exons.index(1)+ncodingexons) ## number of 3'UTR exons
                    except:     ## no coding exons
                        UTR=0

                    ## find CDS and exon interval numbers
                    flag1=0
                    flag2=0
                    CDSpos=-1        ## this gives the CDSpos 0-based: i.e. first CDS is index 0
                    for i in range(0,len(l)):
                        if start>=l[i][0] and start<=l[i][1]:
                            CDSpos = i if ispositivestr else len(l)-i-1
                        if start>=l[i][0] and end<=l[i][1]:
                            flag1 = 1   ##indel is completely contained in CDS
                            break
                    
                    exonpos=-1       ## this gives the exonpos also 0-based
                    for i in range(0,len(m)):
                        if start>=m[i][0] and start<=m[i][1]:
                            exonpos = i if ispositivestr else len(m)-i-1
                        if start>=m[i][0] and end<=m[i][1]:
                            flag2 = 1   ##indel is completely contained in exon
                            break
                    if CDSpos==-1 or exonpos==-1:   ##start position of indel was not in ANY intervals
                        outdata["causes NMD?"] = "no exons or no CDS containing start of indel"
#########################################################
                        o_lof.write('\t'+'\t'.join(outdata[i] for i in LOFparams) + '\n')
#########################################################
                        continue

                    exonindex= exonpos if ispositivestr else len(m)-exonpos-1
                    CDSindex= CDSpos if ispositivestr else len(l)-CDSpos-1

                    codingpos = exonpos-coding_exons.index(1)      ## this gives coding exon position 0-based

                    diff = len(subst)-len(data[3])
                    if ispositivestr:
                        ## 1-based position of indel in CDS coordinates
                        newCDSpos = CDSprec[CDSpos] + start - l[CDSindex][0] + 1
                        ## 1-based position of indel in exon coordinates
                        newexonpos = exonprec[exonpos] + start - m[exonindex][0] + 1
                    else:
                        newCDSpos = CDSprec[CDSpos] + l[CDSindex][1] - start + 1
                        newexonpos = exonprec[exonpos] + m[exonindex][1] - start + 1
                    ## # of exon nucleotides before e-e junction
                    if newexonpos-1<exonprec[-1]:       ##indel being before last e-e junction shifts e-e position
                        juncpos = exonprec[-1]+diff     ##WRONG IF START POSITION IS LAST NUCLEOTIDE BEFORE E-E AND
                                                        ##IS DELETION (WOULD BE SPLICE OVERLAP)
                    else:                               ##indel is after last junction, position unchanged
                        juncpos = exonprec[-1]
                    outdata["indel position in CDS"] = `newCDSpos`
                    
                    lastindex = -1 if ispositivestr else 0
                    indeltoend = exonprec[-1]+m[lastindex][1]-m[lastindex][0]+1 + diff - (newexonpos-1) ##CHECK THIS EXTRA +1
                    if flag1==0:
                        outdata["causes NMD?"] = "no CDS regions completely containing variant"
#########################################################
                        o_lof.write('\t'+'\t'.join(outdata[i] for i in LOFparams) + '\n')
#########################################################
                        continue
                    if flag2==0:
                        outdata["causes NMD?"] = "no exon regions completely containing variant"
#########################################################
                        o_lof.write('\t'+'\t'.join(outdata[i] for i in LOFparams) + '\n')
#########################################################
                        continue
                        
                    if ispositivestr:
                        modCDSseq = CDSseq[0:newCDSpos-1]
                        modCDSseq += subst
                        modCDSseq += CDSseq[newCDSpos-1+len(data[3]):]
                    else:
                        modCDSseq = CDSseq[0:newCDSpos-len(data[3])]
                        modCDSseq += compstr(subst)
                        modCDSseq += CDSseq[newCDSpos:]
                    ref_aa = translate_aa(CDSseq)
                    alt_aa = translate_aa(modCDSseq)

                    try:
                        nextATG = `3*(alt_aa[:1].index('M')+1)`
                    except:
                        nextATG = 'N/A'
                    
                    ## # of CDS nucleotides before stop codon in alternate sequence
                    try: stopCDS = 3*alt_aa.index('*')
                    except:
                        outdata["causes NMD?"] = "No stop codon found in alt_aa"
#########################################################
                        o_lof.write('\t'+'\t'.join(outdata[i] for i in LOFparams) + '\n')
#########################################################
                        continue

                    ## stopexon is # of exon nucleotides preceding first nucleotide of stop codon
                    ## increxon is the exon position (not exon index) where the new stop occurs

                    ## if is in very last CDS or STOP is in current CDS
                    if CDSpos==len(l)-1 or (stopCDS>=CDSprec[CDSpos] and stopCDS<CDSprec[CDSpos+1]+diff):
                        increxon = exonpos
                        if ispositivestr:
                            stopexon = exonprec[exonpos]+l[CDSpos][0]-m[exonpos][0]+stopCDS-CDSprec[CDSpos]
                        else:
                            stopexon = exonprec[exonpos]+m[exonindex][1]-l[CDSindex][1]+stopCDS-CDSprec[CDSpos]
                    else:
                        incrCDS = CDSpos
                        while incrCDS<len(l):
                            increxon = CDS2ex[incrCDS]
                            if incrCDS==len(l)-1 or (stopCDS>=CDSprec[incrCDS]+diff and stopCDS<CDSprec[incrCDS+1]+diff):
                                if ispositivestr:
                                    stopexon = exonprec[increxon]+l[incrCDS][0]-m[increxon][0]+stopCDS-(CDSprec[incrCDS]+diff)
                                else:
                                    stopexon = exonprec[increxon]+m[len(m)-increxon-1][1]-l[len(l)-incrCDS-1][1]+stopCDS-(CDSprec[incrCDS]+diff)
                                break
                            incrCDS+=1
                    incrcoding = sum(coding_exons[:increxon])   ##incrcoding is the coding exon position where new stop occurs
                    if ncodingexons == 1:
                        incrcodingpos = 'single'
                    elif incrcoding==0:
                        incrcodingpos = 'first'
                    elif incrcoding==ncodingexons-1:
                        incrcodingpos = 'last'
                    else:
                        incrcodingpos = 'middle'

                    ## distances are calculated as follows: TAG_ _| is 5 from exon-exon junction/end of transcript etc.
                    ## end of transcript is denoted as end of last exon.

                    ##number of nucleotides in all exons
                    transcriptend = exonprec[-1]+m[lastindex][1]-m[lastindex][0]+1 + diff    ## in exon coordinates
                    stoptoend = transcriptend - stopexon
                    stoptojunc = juncpos - stopexon
                    indeltoend = transcriptend - (newexonpos-1)
                    NMD = 'YES' if stoptojunc>=dist else 'NO'
                    outdata["causes NMD?"] = NMD

                    ##exon index where new stop occurs
                    increxonindex = increxon if ispositivestr else len(m)-increxon-1

                    if increxon==0:
                        splice1='.'     ## 5' flanking splice site (acceptor)
                    else:
                        if ispositivestr:
                            splice1=c[chr_num][m[increxonindex][0]-2:m[increxonindex][0]].upper()
                        else:
                            splice1=compstr(c[chr_num][m[increxonindex][1]+1:m[increxonindex][1]+3].upper())                
                    if increxon==len(m)-1:
                        splice2='.'     ## 3' flanking splice site (donor)
                    else:
                        if ispositivestr:
                            splice2=c[chr_num][m[increxon][1]+1:m[increxon][1]+3].upper()
                        else:
                            splice2=compstr(c[chr_num][m[increxonindex][0]-2:m[increxonindex][0]].upper())
                        
                    canonical = (splice1=='AG' or splice1=='.') and (splice2=='GT' or splice2=='.')
                    canonical = 'YES' if canonical else 'NO'
                    outdata["5' flanking splice site"] = splice1
                    outdata["3' flanking splice site"] = splice2
                    outdata["canonical?"] = canonical
                    
                    if "prematureStop" in variant:
                        lofPosition = newCDSpos
                    else:
                        lofPosition = stopCDS
                    outdata["stop position in CDS"] = `lofPosition`
                    
#########################################################
                    o_lof.write('\t' + '\t'.join(outdata[i] for i in LOFparams)+'\n')
#########################################################
                        
                    LOFvariants[-1]+=':'+':'.join([splice1+'/'+splice2, `newCDSpos`, `lofPosition`, nextATG,\
                                                   NMD, incrcodingpos]) + pfamDescription

        o2.write('\t'.join(data[k] for k in range(0,7))+'\t')
        allvariants = []
        for variant in LOFvariants:
            allvariants.append(variant)
        for variant in splicevariants:
            allvariants.append(variant)
        for variant in othervariants:
            allvariants.append(variant)
        lineinfo['VA']+=','.join(allvariants) 
        o2.write(';'.join(lineinfo[infotype] for infotype in infotypes)+'\n')
    
    line=infile.readline()
    counter+=1

o2.close()
o_lof.close()
o_splice.close()
infile.close()

print "Finished at: " + datetime.datetime.now().strftime("%H:%M:%S")
