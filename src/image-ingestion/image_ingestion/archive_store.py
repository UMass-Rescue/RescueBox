from typing import Any, cast

from rb.api.database import Archive, ArchiveFile, FileRecord
from sqlmodel import Session, select

_archive_cols = Archive.__table__.columns
_link_cols = ArchiveFile.__table__.columns


def find_archive(session: Session, label: str) -> Archive | None:
    return session.exec(
        select(Archive).where(cast(Any, _archive_cols["label"]) == label)
    ).first()


def create_archive(session: Session, label: str, description: str) -> Archive:
    archive = Archive(label=label, description=description)
    session.add(archive)
    session.flush()
    return archive


def find_or_create_file(session: Session, sha256: str) -> FileRecord:
    record = session.get(FileRecord, sha256)
    if record is None:
        record = FileRecord(sha256=sha256)
        session.add(record)
    return record


def link_files(session: Session, archive: Archive, paths: dict[str, str]) -> None:
    session.flush()
    session.add_all(
        ArchiveFile(archive_id=archive.id, file_sha256=sha256, path=path)
        for path, sha256 in paths.items()
    )


def rename_archive(session: Session, archive: Archive, new_label: str) -> None:
    archive.label = new_label
    session.commit()


def delete_archive(session: Session, archive: Archive, retain_hashes: bool) -> int:
    links = session.exec(
        select(ArchiveFile).where(cast(Any, _link_cols["archive_id"]) == archive.id)
    ).all()
    sha256s = {link.file_sha256 for link in links}
    for link in links:
        session.delete(link)
    session.flush()
    session.delete(archive)
    session.flush()
    if not retain_hashes:
        _delete_unused_files(session, sha256s)
    session.commit()
    return len(links)


def _delete_unused_files(session: Session, sha256s: set[str]) -> None:
    still_used = set(
        session.exec(
            select(ArchiveFile.file_sha256).where(
                cast(Any, _link_cols["file_sha256"]).in_(sha256s)
            )
        ).all()
    )
    for sha256 in sha256s - still_used:
        session.delete(session.get(FileRecord, sha256))
