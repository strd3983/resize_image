import os, imghdr
from PIL import Image


def resize_img_file(file_path):
    # ファイルが画像ファイルかどうかを確認し、画像ファイルではない場合リサイズ処理は行わない
    img_type = imghdr.what(file_path)
    if img_type is None:
        return

    img = Image.open(file_path).convert('RGB')
    fp_remove = file_path

    # 長編サイズが1280px以下のときはスルー
    MAX_SIZE = max(img.width, img.height)
    if MAX_SIZE <= 1280:
        if os.path.splitext(file_path)[1] == '.png':
            file_path = os.path.join(
                os.path.dirname(file_path),
                os.path.splitext(os.path.basename(file_path))[0] + '.jpg')
            img.save(file_path, "JPEG")
            del img
            os.remove(fp_remove)
        return
    elif img.width > img.height:
        img_resize = img.resize((1280, round(img.height * 1280 / img.width)),
                                Image.LANCZOS)
    else:
        img_resize = img.resize((round(img.width * 1280 / img.height), 1280),
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
