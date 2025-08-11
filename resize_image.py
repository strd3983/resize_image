import configparser
import ctypes
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageFile, UnidentifiedImageError
from tqdm import tqdm

version = "v5.0"


# --------------------------------------------------
# メイン関数
# --------------------------------------------------
def main() -> None:
    print("\n画像圧縮 by Python")
    print(f"Version:{version}\n")
    rSIZE = 1280  # リサイズサイズ
    rTYPE = 6  # フィルタタイプ
    rTHRED = 8  # スレッド数
    rSIZE, rTYPE, rTHRED = config()
    if rSIZE <= 0 or rTYPE < 0 or 5 < rTYPE:
        print("E: setting.iniの値が不適切です\n")
        return

    base_dir = rel2abs_path("", "exe")
    fps = [fp for fp in base_dir.rglob("*") if fp.is_file() and is_image_file(fp)]

    try:
        with tqdm(total=len(fps), unit=" file") as pbar:
            tasks = []
            with ThreadPoolExecutor(max_workers=rTHRED) as executor:
                for fp in fps:
                    task = executor.submit(resize_img_file, fp, rSIZE, rTYPE)
                    tasks.append(task)
                for _ in as_completed(tasks):
                    pbar.update(1)
    except OSError as e:
        print(f"\nE: 画像読み込みエラー: {e}")


# --------------------------------------------------
# 相対パスを絶対パスに変換
# --------------------------------------------------
def rel2abs_path(filename: str, attr: str) -> Path:
    if attr == "temp":
        datadir = Path(__file__).parent
    elif attr == "exe":
        datadir = Path(sys.argv[0]).parent
    else:
        raise Exception(f"E: 相対パスの引数ミス [{attr}]")
    return (datadir / filename).resolve()


# --------------------------------------------------
# iniファイルの読み込み
# --------------------------------------------------
def config() -> Tuple[int, int, int]:
    rSIZE = 0
    rTYPE = 6
    config_ini = configparser.ConfigParser()
    config_ini_path = rel2abs_path("setting.ini", "exe")
    if config_ini_path.exists():
        with config_ini_path.open(encoding="utf-8") as fp:
            config_ini.read_file(fp)
            read_default = config_ini["DEFAULT"]
            rSIZE = int(read_default.get("長辺サイズ"))
            rTYPE = int(read_default.get("アルゴリズム"))
            rTHRED = int(read_default.get("スレッド数"))
            print("###---------------------------------###")
            print("長辺サイズ:", rSIZE)
            print("リサイズアルゴリズム:", rTYPE)
            print("スレッド数:", rTHRED)
            print("###---------------------------------###")
            return rSIZE, rTYPE, rTHRED
    else:
        print("E: setting.iniが見つかりません\n")
        return 0, 6, 0


# --------------------------------------------------
# 画像判定
# --------------------------------------------------
def is_image_file(filepath: Path) -> bool:
    try:
        img = Image.open(filepath)
        img.verify()
        return True
    except (IOError, SyntaxError, UnidentifiedImageError):
        return False
    except Exception as e:
        print(f"{filepath}: {e}")
        return False


# --------------------------------------------------
# ファイル属性解除（Windows）
# --------------------------------------------------
def unsetReadonlyAttrib(fp: Path) -> None:
    FILE_ATTRIBUTE_HIDDEN = 2
    FILE_ATTRIBUTE_READONLY = 1
    TARGETBITS = FILE_ATTRIBUTE_READONLY + FILE_ATTRIBUTE_HIDDEN
    REV_TARGETBITS = ~TARGETBITS

    val = ctypes.windll.kernel32.GetFileAttributesW(str(fp))
    if 0 != (val & 3):
        val = val & REV_TARGETBITS
        ctypes.windll.kernel32.SetFileAttributesW(str(fp), val)


# --------------------------------------------------
# リサイズ処理
# --------------------------------------------------
def resize_img_file(fp: Path, rSIZE: int, rTYPE: int) -> None:
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    if not is_image_file(fp):
        return

    unsetReadonlyAttrib(fp)
    img = Image.open(fp).convert("RGB")

    if max(img.width, img.height) <= rSIZE:
        img_resize = img
    elif img.width > img.height:
        lSIZE = round(img.height * rSIZE / img.width)
        img_resize = img.resize((rSIZE, lSIZE), rTYPE)
    else:
        lSIZE = round(img.width * rSIZE / img.height)
        img_resize = img.resize((lSIZE, rSIZE), rTYPE)

    convert_type(fp, img_resize)


# --------------------------------------------------
# png, webp → jpg 変換
# --------------------------------------------------
def convert_type(fp: Path, img) -> None:
    ext = fp.suffix.lower()
    fp.unlink()
    if ext in {".png", ".webp"}:
        fp = fp.with_suffix(".jpg")
    img.save(fp, "JPEG")
    del img


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("E: ", e)
    print("M: 終了しました")
    input("Press Enter to continue...")
