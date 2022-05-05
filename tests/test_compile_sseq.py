import SDATtool2.sseq
import hexdump
import difflib

SEQNAME = 'SEQ_GS_P_EYE_ROCKET'
prefix = f'gs_sound_data/Files/SEQ/{SEQNAME}'
txtfilename = f'{prefix}.txt'
sseqfilename = f'{prefix}.sseq'

with open(txtfilename) as txtfile:
    compiled = SDATtool2.sseq.TxtToSseqConverter().compile(txtfile)
with open(sseqfilename, 'rb') as binfile:
    reference = binfile.read()
if compiled != reference:
    revd = [x.format(seqname=SEQNAME) for x in SDATtool2.sseq.SseqToTxtConverter(compiled).parse()]
    with open(txtfilename) as txtfile:
        orig = [x.rstrip('\n') for x in txtfile]
    for line in difflib.unified_diff(orig, revd, fromfile='first', tofile='second'):
        print(line)
