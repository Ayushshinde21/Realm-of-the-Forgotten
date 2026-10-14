# Build a Windows .exe (run on Windows):   pyinstaller VeggieQuest.spec
# Output: dist/VeggieQuest/VeggieQuest.exe  (zip the whole dist/VeggieQuest folder)
block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    datas=[("assets", "assets")],
    hiddenimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="VeggieQuest",
    console=False,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="VeggieQuest")
