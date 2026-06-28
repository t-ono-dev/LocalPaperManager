from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_PAPER_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "title": "TEXT",
    "creators": "TEXT",
    "year": "TEXT",
    "date": "TEXT",
    "publication": "TEXT",
    "journal_abbr": "TEXT",
    "doi": "TEXT UNIQUE",
    "url": "TEXT",
    "date_added": "TEXT NOT NULL",
    "pdf_path": "TEXT",
    "bibtex_key": "TEXT",
    "bibtex_raw": "TEXT",
    "file_hash": "TEXT UNIQUE",
    "notes": "TEXT",
    "volume": "TEXT",
    "pages": "TEXT",
    "issue": "TEXT",
    "publisher": "TEXT",
    "entry_type": "TEXT",
}


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                creators TEXT,
                year TEXT,
                date TEXT,
                publication TEXT,
                journal_abbr TEXT,
                doi TEXT UNIQUE,
                url TEXT,
                date_added TEXT NOT NULL,
                pdf_path TEXT,
                bibtex_key TEXT,
                bibtex_raw TEXT,
                file_hash TEXT UNIQUE,
                notes TEXT,
                volume TEXT,
                pages TEXT,
                issue TEXT,
                publisher TEXT,
                entry_type TEXT
            );
            """
        )

        self.ensure_paper_columns()

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_folders (
                paper_id INTEGER NOT NULL,
                folder_id INTEGER NOT NULL,
                PRIMARY KEY (paper_id, folder_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
            );
            """
        )

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_paper_folders_folder ON paper_folders(folder_id);")
        self.conn.commit()
        self.backfill_urls_from_doi()

    def ensure_paper_columns(self) -> None:
        cur = self.conn.execute("PRAGMA table_info(papers);")
        existing = {row["name"] for row in cur.fetchall()}

        for name, col_type in BASE_PAPER_COLUMNS.items():
            if name in existing or name == "id":
                continue
            plain_type = col_type.replace(" UNIQUE", "").replace(" NOT NULL", "")
            self.conn.execute(f"ALTER TABLE papers ADD COLUMN {name} {plain_type};")

        self.conn.commit()

    def backfill_urls_from_doi(self) -> None:
        cur = self.conn.execute("SELECT id, doi, url FROM papers;")
        for row in cur.fetchall():
            doi = normalize_doi(row["doi"])
            url = empty_to_none(row["url"])
            if doi and not url:
                self.conn.execute(
                    "UPDATE papers SET doi = ?, url = ? WHERE id = ?;",
                    (doi, doi_to_url(doi), row["id"]),
                )
        self.conn.commit()

    # ---------- Folders ----------

    def list_folders(self) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT
                f.id,
                f.name,
                COUNT(pf.paper_id) AS paper_count
            FROM folders f
            LEFT JOIN paper_folders pf ON pf.folder_id = f.id
            GROUP BY f.id, f.name
            ORDER BY LOWER(f.name) ASC;
            """
        )
        return list(cur.fetchall())

    def create_folder(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Folder name is empty.")

        cur = self.conn.execute(
            "INSERT INTO folders(name) VALUES (?);",
            (name,),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def rename_folder(self, folder_id: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("Folder name is empty.")

        self.conn.execute(
            "UPDATE folders SET name = ? WHERE id = ?;",
            (new_name, folder_id),
        )
        self.conn.commit()

    def delete_folder(self, folder_id: int) -> None:
        self.conn.execute("DELETE FROM paper_folders WHERE folder_id = ?;", (folder_id,))
        self.conn.execute("DELETE FROM folders WHERE id = ?;", (folder_id,))
        self.conn.commit()

    def assign_paper_to_folder(self, paper_id: int, folder_id: int) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO paper_folders(paper_id, folder_id)
            VALUES (?, ?);
            """,
            (paper_id, folder_id),
        )
        self.conn.commit()

    def move_paper_to_folder(self, paper_id: int, folder_id: int) -> None:
        self.conn.execute("DELETE FROM paper_folders WHERE paper_id = ?;", (paper_id,))
        self.conn.execute(
            """
            INSERT OR IGNORE INTO paper_folders(paper_id, folder_id)
            VALUES (?, ?);
            """,
            (paper_id, folder_id),
        )
        self.conn.commit()

    def move_papers_to_folder(self, paper_ids: list[int], folder_id: int) -> None:
        for paper_id in paper_ids:
            self.conn.execute("DELETE FROM paper_folders WHERE paper_id = ?;", (paper_id,))
            self.conn.execute(
                """
                INSERT OR IGNORE INTO paper_folders(paper_id, folder_id)
                VALUES (?, ?);
                """,
                (paper_id, folder_id),
            )
        self.conn.commit()

    def remove_paper_from_folder(self, paper_id: int, folder_id: int) -> None:
        self.conn.execute(
            "DELETE FROM paper_folders WHERE paper_id = ? AND folder_id = ?;",
            (paper_id, folder_id),
        )
        self.conn.commit()

    def remove_papers_from_folder(self, paper_ids: list[int], folder_id: int) -> None:
        for paper_id in paper_ids:
            self.conn.execute(
                "DELETE FROM paper_folders WHERE paper_id = ? AND folder_id = ?;",
                (paper_id, folder_id),
            )
        self.conn.commit()

    # ---------- Papers ----------

    def list_papers(self, folder_id: int | None = None, unfiled: bool = False) -> list[sqlite3.Row]:
        if folder_id is not None:
            cur = self.conn.execute(
                """
                SELECT p.*
                FROM papers p
                INNER JOIN paper_folders pf ON pf.paper_id = p.id
                WHERE pf.folder_id = ?
                ORDER BY p.date_added DESC, p.id DESC;
                """,
                (folder_id,),
            )
            return list(cur.fetchall())

        if unfiled:
            cur = self.conn.execute(
                """
                SELECT p.*
                FROM papers p
                LEFT JOIN paper_folders pf ON pf.paper_id = p.id
                WHERE pf.folder_id IS NULL
                ORDER BY p.date_added DESC, p.id DESC;
                """
            )
            return list(cur.fetchall())

        cur = self.conn.execute(
            """
            SELECT *
            FROM papers
            ORDER BY date_added DESC, id DESC;
            """
        )
        return list(cur.fetchall())

    def get_paper(self, paper_id: int) -> sqlite3.Row | None:
        cur = self.conn.execute("SELECT * FROM papers WHERE id = ?;", (paper_id,))
        return cur.fetchone()

    def get_papers_by_ids(self, paper_ids: list[int]) -> list[sqlite3.Row]:
        if not paper_ids:
            return []
        placeholders = ",".join("?" for _ in paper_ids)
        cur = self.conn.execute(
            f"SELECT * FROM papers WHERE id IN ({placeholders});",
            paper_ids,
        )
        rows = list(cur.fetchall())
        order = {pid: i for i, pid in enumerate(paper_ids)}
        rows.sort(key=lambda r: order.get(int(r["id"]), 10**9))
        return rows

    def get_pdf_path(self, paper_id: int) -> str | None:
        row = self.get_paper(paper_id)
        if row is None:
            return None
        return row["pdf_path"]

    def update_paper(self, paper_id: int, updates: dict[str, Any]) -> None:
        allowed = {
            "title",
            "creators",
            "year",
            "date",
            "publication",
            "journal_abbr",
            "doi",
            "url",
            "pdf_path",
            "bibtex_key",
            "bibtex_raw",
            "notes",
            "volume",
            "pages",
            "issue",
            "publisher",
            "entry_type",
        }

        updates = {k: empty_to_none(v) for k, v in updates.items() if k in allowed}

        if "doi" in updates:
            updates["doi"] = normalize_doi(updates["doi"])

        doi = updates.get("doi")
        if doi and not updates.get("url"):
            updates["url"] = doi_to_url(doi)

        if not updates:
            return

        assignments = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [paper_id]

        self.conn.execute(f"UPDATE papers SET {assignments} WHERE id = ?;", values)
        self.conn.commit()

    def delete_paper(self, paper_id: int) -> None:
        self.delete_papers([paper_id])

    def delete_papers(self, paper_ids: list[int]) -> None:
        for paper_id in paper_ids:
            self.conn.execute("DELETE FROM paper_folders WHERE paper_id = ?;", (paper_id,))
            self.conn.execute("DELETE FROM papers WHERE id = ?;", (paper_id,))
        self.conn.commit()

    def upsert_pdf_stub(self, record: dict[str, Any], folder_id: int | None = None) -> int:
        record = dict(record)
        record["doi"] = normalize_doi(record.get("doi"))
        if record.get("doi") and not record.get("url"):
            record["url"] = doi_to_url(record["doi"])

        file_hash = record.get("file_hash")
        if file_hash:
            cur = self.conn.execute("SELECT id FROM papers WHERE file_hash = ?;", (file_hash,))
            row = cur.fetchone()
            if row:
                paper_id = int(row["id"])
                self.conn.execute(
                    """
                    UPDATE papers
                    SET pdf_path = COALESCE(pdf_path, ?),
                        doi = COALESCE(?, doi),
                        url = COALESCE(?, url)
                    WHERE id = ?;
                    """,
                    (record.get("pdf_path"), record.get("doi"), record.get("url"), paper_id),
                )
                self.conn.commit()
                if folder_id is not None:
                    self.assign_paper_to_folder(paper_id, folder_id)
                return paper_id

        cur = self.conn.execute(
            """
            INSERT INTO papers (
                title, creators, year, date, publication, journal_abbr,
                doi, url, date_added, pdf_path, bibtex_key, bibtex_raw, file_hash,
                notes, volume, pages, issue, publisher, entry_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                record.get("title"),
                record.get("creators"),
                record.get("year"),
                record.get("date"),
                record.get("publication"),
                record.get("journal_abbr"),
                record.get("doi"),
                record.get("url"),
                record["date_added"],
                record.get("pdf_path"),
                record.get("bibtex_key"),
                record.get("bibtex_raw"),
                record.get("file_hash"),
                record.get("notes"),
                record.get("volume"),
                record.get("pages"),
                record.get("issue"),
                record.get("publisher"),
                record.get("entry_type"),
            ),
        )
        self.conn.commit()
        paper_id = int(cur.lastrowid)
        if folder_id is not None:
            self.assign_paper_to_folder(paper_id, folder_id)
        return paper_id

    def upsert_bibtex_record(self, record: dict[str, Any], folder_id: int | None = None) -> int:
        record = dict(record)
        doi = normalize_doi(record.get("doi"))
        record["doi"] = doi
        if doi and not record.get("url"):
            record["url"] = doi_to_url(doi)

        bibtex_key = record.get("bibtex_key")
        existing_id: int | None = None

        if doi:
            cur = self.conn.execute("SELECT id FROM papers WHERE doi = ?;", (doi,))
            row = cur.fetchone()
            if row:
                existing_id = int(row["id"])

        if existing_id is None and bibtex_key:
            cur = self.conn.execute("SELECT id FROM papers WHERE bibtex_key = ?;", (bibtex_key,))
            row = cur.fetchone()
            if row:
                existing_id = int(row["id"])

        if existing_id is not None:
            self.conn.execute(
                """
                UPDATE papers
                SET
                    title = COALESCE(?, title),
                    creators = COALESCE(?, creators),
                    year = COALESCE(?, year),
                    date = COALESCE(?, date),
                    publication = COALESCE(?, publication),
                    journal_abbr = COALESCE(?, journal_abbr),
                    doi = COALESCE(?, doi),
                    url = COALESCE(?, url),
                    bibtex_key = COALESCE(?, bibtex_key),
                    bibtex_raw = COALESCE(?, bibtex_raw),
                    notes = COALESCE(?, notes),
                    volume = COALESCE(?, volume),
                    pages = COALESCE(?, pages),
                    issue = COALESCE(?, issue),
                    publisher = COALESCE(?, publisher),
                    entry_type = COALESCE(?, entry_type)
                WHERE id = ?;
                """,
                (
                    empty_to_none(record.get("title")),
                    empty_to_none(record.get("creators")),
                    empty_to_none(record.get("year")),
                    empty_to_none(record.get("date")),
                    empty_to_none(record.get("publication")),
                    empty_to_none(record.get("journal_abbr")),
                    doi,
                    empty_to_none(record.get("url")),
                    empty_to_none(record.get("bibtex_key")),
                    empty_to_none(record.get("bibtex_raw")),
                    empty_to_none(record.get("notes")),
                    empty_to_none(record.get("volume")),
                    empty_to_none(record.get("pages")),
                    empty_to_none(record.get("issue")),
                    empty_to_none(record.get("publisher")),
                    empty_to_none(record.get("entry_type")),
                    existing_id,
                ),
            )
            self.conn.commit()
            if folder_id is not None:
                self.assign_paper_to_folder(existing_id, folder_id)
            return existing_id

        cur = self.conn.execute(
            """
            INSERT INTO papers (
                title, creators, year, date, publication, journal_abbr,
                doi, url, date_added, pdf_path, bibtex_key, bibtex_raw, file_hash,
                notes, volume, pages, issue, publisher, entry_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                record.get("title"),
                record.get("creators"),
                record.get("year"),
                record.get("date"),
                record.get("publication"),
                record.get("journal_abbr"),
                doi,
                record.get("url"),
                record["date_added"],
                record.get("pdf_path"),
                record.get("bibtex_key"),
                record.get("bibtex_raw"),
                record.get("file_hash"),
                record.get("notes"),
                record.get("volume"),
                record.get("pages"),
                record.get("issue"),
                record.get("publisher"),
                record.get("entry_type"),
            ),
        )
        self.conn.commit()
        paper_id = int(cur.lastrowid)
        if folder_id is not None:
            self.assign_paper_to_folder(paper_id, folder_id)
        return paper_id


def normalize_doi(value: Any) -> str | None:
    if value is None:
        return None

    doi = str(value).strip()
    if not doi:
        return None

    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")
    doi = doi.strip().strip(".;,")
    doi = doi.lower()

    return doi or None


def doi_to_url(doi: str | None) -> str | None:
    doi = normalize_doi(doi)
    if not doi:
        return None
    return f"https://doi.org/{doi}"


def empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return value
