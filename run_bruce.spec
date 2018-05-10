# -*- mode: python -*-

block_cipher = None


a = Analysis(['sqaTools.py'],
             pathex=['D:\\bruce\\workspace\\sqaTools'],
             binaries=[],
             datas=[('.\\templates',''), 
					('.\\static',''), 
					('.\\config',''), 
					('.\\data',''),
					('.\\geckodriver.exe','')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='sqaTools',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='static\images\sound_speaker_48px.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='run')
