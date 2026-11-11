"""Вспомогательные функции: сборка тестового APKINDEX.tar.gz."""

import gzip
import io
import pathlib
import tarfile

INDEX_TEXT = """C:Q1aaa=
P:app
V:1.0-r0
D:lib>=1.0 so:libc.musl-x86_64.so.1 !conflict cmd:tool app so:libfoo.so.1
p:cmd:app=1.0

C:Q1bbb=
P:lib
V:2.0-r1
D:so:libc.musl-x86_64.so.1
p:so:libfoo.so.1=1

C:Q1ccc=
P:tool
V:0.5-r0
p:cmd:tool=0.5

C:Q1ddd=
P:musl
V:1.2-r0
p:so:libc.musl-x86_64.so.1=1

C:Q1eee=
P:app
V:0.9-r0
"""


def tar_segment(name, data):
    """Возвращает кусок tar без завершающих нулевых блоков."""
    info = tarfile.TarInfo(name)
    info.size = len(data)
    header = info.tobuf(tarfile.GNU_FORMAT, "utf-8", "surrogateescape")
    return header + data + bytes(-len(data) % tarfile.BLOCKSIZE)


def make_archive(text=INDEX_TEXT):
    """Собирает архив из двух gzip-частей, как в настоящем репозитории."""
    signature = gzip.compress(tar_segment(".SIGN.RSA.key", b"signature"))
    body = io.BytesIO()
    with tarfile.open(fileobj=body, mode="w") as tar:
        data = text.encode("utf-8")
        info = tarfile.TarInfo("APKINDEX")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return signature + gzip.compress(body.getvalue())


def write_repository(folder, archive=None):
    """Создаёт в папке репозиторий и возвращает его file://-адрес."""
    path = pathlib.Path(folder)
    (path / "APKINDEX.tar.gz").write_bytes(archive or make_archive())
    return path.as_uri()
