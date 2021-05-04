import os
import ctypes
import imghdr
from PIL import Image

FILE_ATTRIBUTE_HIDDEN: int = 2
FILE_ATTRIBUTE_READONLY: int = 1
TARGETBITS: int = FILE_ATTRIBUTE_READONLY + FILE_ATTRIBUTE_HIDDEN
REV_TARGETBITS = ~TARGETBITS
rSIZE: int = 1280


# ファイルが画像かどうか判定する
def file_type(file_path):
    f = open(file_path, 'rb')
    f_head = f.read()[:2]
    f.close()
    if f_head == b'\xff\xd8':
        return 'jpeg'
    else:
        return imghdr.what(file_path)


# WindowsファイルのReadonlyと隠し属性を未設定状態に設定する。
def unsetReadonlyAttrib(file_path):
    # Windowsファイル属性を取得
    val: int = ctypes.windll.kernel32.GetFileAttributesW(file_path)
    if 0 != (val & 3):
        val = val & REV_TARGETBITS
        # Windowsファイル属性を再設定
        ctypes.windll.kernel32.SetFileAttributesW(file_path, val)


def resize_img_file(file_path):
    # ファイルが画像ファイルかどうかを確認し、画像ファイルではない場合リサイズ処理は行わない
    img_type = file_type(file_path)
    if img_type is None:
        return

    # 指定パスのファイル属性を解除
    unsetReadonlyAttrib(file_path)
    img = Image.open(file_path).convert('RGB')
    fp_remove = file_path

    # 長編サイズが1280px(rSIZE)以下のときはスルー
    MAX_SIZE = max(img.width, img.height)
    if MAX_SIZE <= rSIZE:
        if img_type == 'png':
            file_path = os.path.join(
                os.path.dirname(file_path),
                os.path.splitext(os.path.basename(file_path))[0] + '.jpg')
            img.save(file_path, "JPEG")
            del img
            os.remove(fp_remove)
        return
    elif img.width > img.height:
        img_resize = img.resize((rSIZE, round(img.height * rSIZE / img.width)),
                                Image.LANCZOS)
    else:
        img_resize = img.resize((round(img.width * rSIZE / img.height), rSIZE),
                                Image.LANCZOS)

    # ファイル名が.pngである場合.jpgに変換
    if os.path.splitext(file_path)[1] == '.png':
        file_path = os.path.join(
            os.path.dirname(file_path),
            os.path.splitext(os.path.basename(file_path))[0] + '.jpg')
        img_resize.save(file_path, "JPEG")
        del img
        os.remove(fp_remove)
    else:
        img_resize.save(file_path, "JPEG")
        del img


def recursive_resize_img_file(file_path):
    if os.path.isdir(file_path):
        print(file_path)
        files = os.listdir(file_path)
        for file in files:
            recursive_resize_img_file(os.path.join(file_path, file))
    else:
        resize_img_file(file_path)


dir = os.getcwd()
recursive_resize_img_file(dir)
