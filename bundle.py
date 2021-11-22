import os, sys, platform, shutil
from argparse import ArgumentParser

from autooed.utils.path import get_version


system = platform.system()
if system == 'Darwin':
    icon_fmt = 'icns'
elif system == 'Windows':
    icon_fmt = 'ico'
elif system == 'Linux':
    icon_fmt = 'svg'
else:
    raise NotImplementedError


spec_str = \
"""
# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['../../run_gui.py'],
             pathex=[],
             binaries=[],
             datas=[('../../autooed/problem/custom', 'autooed/problem/custom'), ('../../autooed/problem/predefined', 'autooed/problem/predefined'), ('../../examples', 'examples'), ('../../static', 'static')],
             hiddenimports=['PIL._tkinter_finder', 'pymoo.cython.non_dominated_sorting', 'sklearn.neighbors._typedefs', 'sklearn.neighbors._quad_tree', 'sklearn.tree._utils', 'sklearn.utils._cython_blas'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='AutoOED_{version}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='../../static/icon.{icon_fmt}')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='AutoOED_{version}')
"""

if system == 'Darwin':
    spec_str += \
"""
app = BUNDLE(coll,
            name='AutoOED.app',
            icon='../../static/icon.{icon_fmt}',
            bundle_identifier='com.autooed',
            info_plist={
                'NSPrincipalClass': 'NSApplication',
                'NSAppleScriptEnabled': False,
                'CFBundleDocumentTypes': [
                    {
                        'CFBundleTypeName': 'AutoOED',
                        'CFBundleTypeIconFile': '../../static/icon.{icon_fmt}',
                        'LSItemContentTypes': ['com.autooed.autooed'],
                        'LSHandlerRank': 'Owner'
                    }
                ]
            })
"""
else:
    spec_str += \
"""
app = BUNDLE(coll,
            name='AutoOED.app',
            icon='../../static/icon.{icon_fmt}',
            bundle_identifier=None)
"""

spec_str = spec_str.replace('{version}', get_version()).replace('{icon_fmt}', icon_fmt)


def main():

    '''
    Parse bundle type from command input
    '''

    parser = ArgumentParser()
    parser.add_argument(
        '--zip',
        default=False,
        action='store_true',
    )
    args = parser.parse_args()

    base_dir = './bundle'
    build_dir = os.path.join(base_dir, 'build')
    dist_dir = os.path.join(base_dir, 'dist')
    spec_dir = os.path.join(base_dir, 'spec')
    spec_path = os.path.join(spec_dir, 'AutoOED.spec')

    for work_dir in [base_dir, build_dir, dist_dir, spec_dir]:
        os.makedirs(work_dir, exist_ok=True)

    with open(spec_path, 'w') as fp:
        fp.write(spec_str)

    cmd = f'pyinstaller --workpath {build_dir} --distpath {dist_dir} --noconfirm {spec_path}'
    os.system(cmd)

    if args.zip:
        if system == 'Darwin':
            os.system(f"cd {dist_dir} && zip -r {os.path.join('..', 'AutoOED')}.zip ./AutoOED.app")
        else:
            shutil.make_archive(os.path.join(base_dir, 'AutoOED'), 'zip', root_dir=dist_dir, base_dir='AutoOED')


if __name__ == '__main__':
    main()
