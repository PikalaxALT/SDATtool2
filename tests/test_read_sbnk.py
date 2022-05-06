from SDATtool2.sbnk import SNDBankData

name = 'BANK_BGM_ARCEUS'
with open(f'gs_sound_data/Files/BANK/{name}.sbnk', 'rb') as fp:
    bank = SNDBankData.from_binary(fp.read())

print(bank)
