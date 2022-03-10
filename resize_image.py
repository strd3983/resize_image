import os
import ctypes
import imghdr
import configparser
from PIL import Image

version = 'v3.2'
Image.LOAD_TRUNCATED_IMAGES = True
FILE_ATTRIBUTE_HIDDEN: int = 2
FILE_ATTRIBUTE_READONLY: int = 1
TARGETBITS: int = FILE_ATTRIBUTE_READONLY + FILE_ATTRIBUTE_HIDDEN
REV_TARGETBITS = ~TARGETBITS


# --------------------------------------------------
# メイン関数
# --------------------------------------------------
def main():
    print('\n画像圧縮 by Python')
    print(f'Version:{version}\n')
    rSIZE = 0  # リサイズサイズ
    rTYPE = 6  # フィルタタイプ
    rSIZE, rTYPE = config()
    if rSIZE <= 0 or rTYPE < 0 or 5 < rTYPE:
        print('E: setting.iniの値が不適切です\n')
        return
    try:
        recursive_resize_img_file(rel2abs_path('', 'exe'), rSIZE, rTYPE)
    except OSError:
        print('E: 画像読み込みエラー')


# --------------------------------------------------
# 絶対パスを相対パスに [入:相対パス, 実行ファイル側or展開フォルダ側 出:絶対パス]
# --------------------------------------------------
def rel2abs_path(filename, attr):
    import sys
    if attr == 'temp':  # 展開先フォルダと同階層
        datadir = os.path.dirname(__file__)
    elif attr == 'exe':  # exeファイルと同階層の絶対パス
        datadir = os.path.dirname(sys.argv[0])
    else:
        raise print(f'E: 相対パスの引数ミス [{attr}]')
    return os.path.join(datadir, filename)


# --------------------------------------------------
# read_file()関数によるiniファイルの読み込み
# --------------------------------------------------
def config():
    rSIZE = 0  # リサイズサイズ
    rTYPE = 6  # フィルタタイプ
    config_ini = configparser.ConfigParser()
    config_ini_path = rel2abs_path('setting.ini', 'exe')
    # iniファイルが存在するかチェック
    if os.path.exists(config_ini_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_ini_path, encoding='utf-8') as fp:
            config_ini.read_file(fp)
            # iniの値取得
            read_default = config_ini['DEFAULT']
            rSIZE = read_default.get('長辺サイズ')
            rTYPE = read_default.get('アルゴリズム')
            # 設定出力
            print('###---------------------------------###')
            print('長辺サイズ:', rSIZE)
            print('リサイズアルゴリズム:', rTYPE)
            print('###---------------------------------###')
            return int(rSIZE), int(rTYPE)
    else:
        print('E: setting.iniが見つかりません\n')
        return 0, 6


# --------------------------------------------------
# ファイル探索
# --------------------------------------------------
def recursive_resize_img_file(fp, rSIZE, rTYPE):
    if os.path.isdir(fp):  # ディレクトリだった場合
        print(fp)
        files = os.listdir(fp)
        for file in files:
            recursive_resize_img_file(os.path.join(fp, file), rSIZE, rTYPE)
    else:  # ファイルだった場合
        resize_img_file(fp, rSIZE, rTYPE)


# --------------------------------------------------
# ファイルの画像判定
# --------------------------------------------------
def file_type(fp):
    f = open(fp, 'rb')
    f_head = f.read()[:2]
    f.close()
    if f_head == b'\xff\xd8':
        return 'jpeg'
    else:
        return imghdr.what(fp)


# --------------------------------------------------
# ファイルの属性解除
# --------------------------------------------------
def unsetReadonlyAttrib(fp):
    # Windowsファイル属性を取得
    val: int = ctypes.windll.kernel32.GetFileAttributesW(fp)
    if 0 != (val & 3):
        val = val & REV_TARGETBITS
        # Windowsファイル属性を再設定
        ctypes.windll.kernel32.SetFileAttributesW(fp, val)


# --------------------------------------------------
# リサイズ処理
# --------------------------------------------------
def resize_img_file(fp, rSIZE, rTYPE):
    # ファイルが画像ファイルかどうかを確認し、画像ファイルではない場合リサイズ処理は行わない
    img_type = file_type(fp)
    if img_type is None:
        return

    # 指定パスのファイル属性を解除
    unsetReadonlyAttrib(fp)
    img = Image.open(fp).convert('RGB')

    # 長編サイズがrSIZE px以下のときはスルー
    MAX_SIZE = max(img.width, img.height)
    if MAX_SIZE <= rSIZE:
        convert_type(fp, img)
        return
    elif img.width > img.height:
        lSIZE = round(img.height * rSIZE / img.width)
        img_resize = img.resize((rSIZE, lSIZE), rTYPE)
    else:
        lSIZE = round(img.width * rSIZE / img.height)
        img_resize = img.resize((lSIZE, rSIZE), rTYPE)
    convert_type(fp, img_resize)


# --------------------------------------------------
# ファイルが.pngである場合.jpgに変換
# --------------------------------------------------
def convert_type(fp, img):
    fp_remove = fp
    if os.path.splitext(fp)[1] == '.png':
        fp = os.path.join(os.path.dirname(fp),
                          os.path.splitext(os.path.basename(fp))[0] + '.jpg')
        img.save(fp, "JPEG")
        del img
        os.remove(fp_remove)
    else:
        img.save(fp, "JPEG")
        del img


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('E: ', e)
    print('M: 終了しました')
    os.system('PAUSE')
