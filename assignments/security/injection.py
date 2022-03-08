def write_to_jpg(path: str, message: str):
    with open("repins.jpg", 'ab') as img:
        img.write(b"")


def read_from_jpg(path: str):
    with open(path, 'rb') as img:
        readFrom = img.read()
        offset = readFrom.index(bytes.fromhex('FFD9'))
        img.seek(offset + 2)
        print(img.read())


def inject_program_to_jpg(pathpic: str, pathprogram: str):
    with open(pathpic, 'ab') as img, open(pathprogram, 'rb') as program:
        img.write(program.read())
