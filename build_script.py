import base64
import subprocess
from io import BytesIO

from PIL import Image

from gui import base64_icon


def base64_to_ico(base64_str, output_file):
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    image.save(output_file, format='ICO')


def create_executable():
    output_file = "icon.ico"
    base64_to_ico(base64_icon, output_file)
    pyinstaller_command = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--icon', output_file,
        'main.py'
    ]
    result = subprocess.run(pyinstaller_command,
                            capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)


if __name__ == '__main__':
    create_executable()
