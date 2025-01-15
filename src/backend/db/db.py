import sqlite3
import numpy as np
from pathlib import Path
from typing import Any
import pickle


class DatabaseManager:
    """
    Class for managing database of corpus content.

    Creates 5 tables:

    - Sentences (with file path, embeddings and group id)
    - Text categories (linked to sentences by id)
    - Meta properties (linked to sentences by file path)
    - Sentence tiers (linked to sentences by id)
    - Subfolders (linked to sentences by file path)

    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def setup(self) -> None:
        if self.db_path.is_file():
            self.db_path.unlink()
        self.connect()
        self._make_tables()

    def connect(self) -> None:
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def _make_tables(self) -> None:
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY,
                sentence TEXT NOT NULL,
                file_path TEXT NOT NULL,
                embedding BLOB,
                group_id INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS text_categories (
                sentence_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (sentence_id) REFERENCES sentences(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_tiers (
                sentence_id INTEGER,
                name TEXT,
                tier TEXT,
                FOREIGN KEY (sentence_id) REFERENCES sentences(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta_properties (
                file_path TEXT NOT NULL,
                label_name TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT,
                UNIQUE(file_path,  name),
                PRIMARY KEY (file_path,  name)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subfolders (
            file_path TEXT NOT NULL,
            subfolder TEXT NOT NULL,  
            UNIQUE(file_path, subfolder) 
        )
        """)
        # Add indices
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path ON sentences(file_path);
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_group_id ON sentences(group_id);
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentence_id_text_categories ON text_categories(sentence_id);
        """)
        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sentence_id_sent_tiers ON sent_tiers(sentence_id);
    """)

        self.connection.commit()

    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        return pickle.dumps(embedding)

    def _deserialize_embedding(self, embedding_blob: bytes) -> np.ndarray:
        return pickle.loads(embedding_blob)

    def insert_file_entry(self, entry: dict[str, Any]) -> None:
        for sd in entry["sent_dicts"]:
            if sd.get("embedding"):
                embedding_entry = self._serialize_embedding(sd["embedding"])
            else:
                embedding_entry = None
            self.cursor.execute(
                """
            INSERT INTO sentences (sentence, file_path, embedding, group_id)
            VALUES (?, ?, ?, ?)
            """,
                (
                    sd["sentence"],
                    str(entry["file_path"]),
                    embedding_entry,
                    sd.get("group_id"),
                ),
            )

            sentence_id = self.cursor.lastrowid

            for name in sd["text_categories"]:
                self.cursor.execute(
                    """
                    INSERT INTO text_categories (sentence_id, name)
                    VALUES (?, ?)
                """,
                    (sentence_id, name),
                )
            for name, tier in sd.get("sent_tiers", {}).items():
                self.cursor.execute(
                    """
                    INSERT INTO sent_tiers (sentence_id, name, tier)
                    VALUES (?, ?, ?)
                """,
                    (sentence_id, name, tier),
                )
        for property in entry["meta_properties"]:
            label_name = property["label_name"]
            name = property["name"]
            value = property["value"]

            if value is None:
                value = None
            elif isinstance(value, (int, float, bool)):
                value = str(value)

            params = label_name, name, value

            # Check if the meta_property for this file_path already exists
            self.cursor.execute(
                """
                SELECT 1 FROM meta_properties WHERE file_path = ? AND label_name = ? AND name = ? AND value = ?
                """,
                (str(entry["file_path"]), *params),
            )

            existing_property = self.cursor.fetchone()

            if not existing_property:
                self.cursor.execute(
                    """
                    INSERT INTO meta_properties (file_path, label_name, name, value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(entry["file_path"]), label_name, name, value),
                )

        for subfolder in entry["subfolders"]:
            self.cursor.execute(
                """
                    INSERT INTO subfolders (file_path, subfolder)
                    VALUES (?, ?)
                    """,
                (str(entry["file_path"]), subfolder),
            )

        self.connection.commit()

    def _fetch_text_categories(self, sentence_id: int) -> list[str]:
        self.cursor.execute(
            """
            SELECT name FROM text_categories WHERE sentence_id = ?
            """,
            (sentence_id,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    def _fetch_sent_tiers(self, sentence_id: int) -> dict[str, dict[str, str]]:
        self.cursor.execute(
            """
            SELECT name, tier FROM sent_tiers WHERE sentence_id = ?
            """,
            (sentence_id,),
        )
        return {row["name"]: row["tier"] for row in self.cursor.fetchall()}

    def _fetch_sent_dict(
        self, row: sqlite3.Row, include_embeddings: bool = False
    ) -> dict[str, Any]:
        sent_dict = {
            "sentence": row["sentence"],
            "file_path": Path(row["file_path"]),
            "group_id": row["group_id"],
            "text_categories": self._fetch_text_categories(row["id"]),
            "sent_tiers": self._fetch_sent_tiers(row["id"]),
        }
        if include_embeddings and row["embedding"]:
            sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])
        return sent_dict

    def _fetch_meta_properties(
        self, file_path_s: Path | list[Path]
    ) -> list[dict[str, Any]] | dict[str, Any]:
        if type(file_path_s) is set:
            meta_properties = {}
            self.cursor.execute(
                f"""
                SELECT file_path, label_name, name, value
                FROM meta_properties
                WHERE file_path IN ({','.join(['?'] * len(file_path_s))})
                """,
                tuple(file_path_s),
            )
            meta_properties = {}
            for row in self.cursor.fetchall():
                file_path = row["file_path"]
                meta_properties.setdefault(file_path, [])
                meta_prop = self.pack_meta_props(row)
                meta_properties[file_path].append(meta_prop)
            return meta_properties

        else:
            file_path = file_path_s
            self.cursor.execute(
                """
                SELECT  label_name, name, value FROM meta_properties WHERE file_path = ?
                """,
                (str(file_path),),
            )
            meta_properties = []
            for row in self.cursor.fetchall():
                meta_properties.append(self.pack_meta_props(row))
            return meta_properties

    def pack_meta_props(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "label_name": row["label_name"],
            "name": row["name"],
            "value": row["value"],
        }

    def get_sents(
        self,
        subfolders: list[str] | str | None = None,
        file_paths: Path | list[Path] | None = None,
        text_categories: list[str] | str | None = None,
        meta_properties: dict[str, Any] | list[dict[str, Any]] | None = None,
        include_embeddings: bool = False,
        include_meta_properties: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves sentences based on any combination of filters: named_subfolder,
            file_path, text_category, and meta_property.
        Args:
            named_subfolder (list[str] | str, optional): Filter by subfolder(s).
                Defaults to None.
            file_path (list[Path] | Path, optional): Filter by file path(s).
                Defaults to None.
            text_category (list[str] | str, optional): Filter by text
                category(ies). Defaults to None.
            meta_property (dict[str, Any], optional): Filter by meta property
                (e.g., label_name, name, value). Defaults to None.
            include_embeddings (bool, optional): Whether to include embeddings
                 in the results. Defaults to False.
            include_meta_properties (bool, optional): Whether to include meta
                properties in the results. Defaults to True.

        Returns:
            dict[str, Any]: A dictionary containing 'sent_dicts' (list of
            sentences with file_path and embeddings) and 'meta_properties' (if
            requested).
        """
        # Build query and parameters
        query = """
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
            """
        query_params = []
        joins = []
        conditions = []

        # Handle named_subfolder filtering
        if subfolders:
            if isinstance(subfolders, str):
                subfolders = [subfolders]
            placeholders = ",".join(["?"] * len(subfolders))
            joins.append("JOIN subfolders sf ON s.file_path = sf.file_path")
            conditions.append(f"sf.subfolder IN ({placeholders})")
            query_params.extend(subfolders)

        # Handle file_path filtering
        if file_paths:
            if isinstance(file_paths, Path):
                file_paths = [file_paths]
            placeholders = ",".join(["?"] * len(file_paths))
            conditions.append(f"s.file_path IN ({placeholders})")
            query_params.extend(str(p) for p in file_paths)

        # Handle text_category filtering
        if text_categories:
            if isinstance(text_categories, str):
                text_categories = [text_categories]
            placeholders = ",".join(["?"] * len(text_categories))
            joins.append("JOIN text_categories tc ON s.id = tc.sentence_id")
            conditions.append(f"tc.name IN ({placeholders})")
            query_params.extend(text_categories)

        # Handle meta_property filtering (label_name, name, value)
        if meta_properties:
            if isinstance(meta_properties, dict):
                meta_properties = [meta_properties]
            for idx, prop in enumerate(meta_properties):
                label_name = prop.get("label_name")
                name = prop.get("name")
                value = prop.get("value")
                min_value = prop.get("min")
                max_value = prop.get("max")

                # Create a unique alias for each meta_properties table join
                alias = f"mp{idx}"

                if label_name and name:
                    joins.append(
                        f"JOIN meta_properties {alias} ON s.file_path = {alias}.file_path"
                    )
                    conditions.append(f"{alias}.label_name = ? AND {alias}.name = ?")
                    query_params.extend([label_name, name])

                    if value is not None:
                        conditions.append(f"{alias}.value = ?")
                        query_params.append(str(value))

                    # Handle range filtering (min and max)
                    if min_value is not None and max_value is not None:
                        conditions.append(f"{alias}.value BETWEEN ? AND ?")
                        query_params.extend([min_value, max_value])
                    elif min_value is not None:
                        conditions.append(f"{alias}.value >= ?")
                        query_params.append(min_value)
                    elif max_value is not None:
                        conditions.append(f"{alias}.value <= ?")
                        query_params.append(max_value)

        # Combine joins and conditions
        if joins:
            query += " " + " ".join(joins)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Execute query
        self.cursor.execute(query, tuple(query_params))
        rows = self.cursor.fetchall()

        results = {"sent_dicts": []}
        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and row["embedding"]:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            # Collect file_paths for meta_property fetching
            file_paths = {row["file_path"] for row in rows}  # type: ignore
            results["meta_properties"] = self._fetch_meta_properties(file_paths)  # type: ignore

        return results

    def get_sents_by_named_subfolder(
        self,
        subfolder: str | list[str],
        include_embeddings: bool = False,
        include_meta_properties: bool = True,
    ) -> dict[str, Any]:
        """
        Same args and return type as get_sents_by_folder except subfolder arg
        is a column value in subfolder table.
        """
        if isinstance(subfolder, str):
            subfolder = [subfolder]  # Ensure subfolder is a list

        # Prepare the query
        placeholders = ",".join(["?"] * len(subfolder))
        query = f"""
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
            JOIN subfolders sf ON s.file_path = sf.file_path
            WHERE sf.subfolder IN ({placeholders})
        """
        self.cursor.execute(query, tuple(subfolder))
        rows = self.cursor.fetchall()

        results = {"sent_dicts": []}
        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and row["embedding"]:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            file_paths = {row["file_path"] for row in rows}
            results["meta_properties"] = self._fetch_meta_properties(file_paths)  # type: ignore

        return results

    def get_sents_by_file_path(
        self,
        file_path: Path,
        include_embeddings: bool = False,
        include_meta_properties: bool = True,
    ) -> dict[str, Any]:
        """
        Returns a dict of sent_dicts and meta_properties where
        sent_dict has sentence, group_id, embedding, and text_labels.

        Args:
            file_path (Path)
            include_embeddings (bool, optional): Whether to include embeddings in
                sent_dicts
            include_meta_properties (bool, optional): Whether to include
                meta_properties. Defaults to True.

        Returns:
            dict[str, Any]
        """
        # Fetch the sentences for the specified file_path
        query = """
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
            WHERE s.file_path = ?
        """
        self.cursor.execute(query, (str(file_path),))
        rows = self.cursor.fetchall()

        results = {"sent_dicts": []}
        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and "embedding" in row:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            meta_properties = self._fetch_meta_properties(file_path)
            results["meta_properties"] = meta_properties  # type: ignore

        return results

    def get_sents_by_folder(
        self,
        folder_path: Path,
        include_meta_properties: bool = True,
        include_embeddings: bool = True,
    ) -> dict[str, Any]:
        """
        Same args and return type as get_sents_by_file_path except that
        meta_properties is a dictionary with file_path keys.
        """
        file_paths = set(str(file) for file in folder_path.rglob("*") if file.is_file())

        # If no files are found in the folder, return an empty result
        if not file_paths:
            return {"sent_dicts": [], "meta_properties": {}}

        # Fetch the sentences for the specified file_paths
        query = """
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
            WHERE s.file_path IN ({})
        """.format(",".join(["?"] * len(file_paths)))

        self.cursor.execute(query, tuple(file_paths))
        rows = self.cursor.fetchall()

        results = {"sent_dicts": []}
        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and row["embedding"]:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            results["meta_properties"] = self._fetch_meta_properties(file_paths)  # type: ignore

        return results

    def get_sents_by_text_category(
        self,
        name: str,
        include_embeddings: bool = False,
        include_meta_properties: bool = True,
    ) -> dict[str, Any]:
        """Same return type as get_sents_by_folder.

        Args:
            name (str):
            include_embeddings (bool, optional):  Defaults to False.
            include_meta_properties (bool, optional):  Defaults to True.

        Returns:
            list[dict[str, Any]]
        """

        sql_query = """
            SELECT s.sentence, s.file_path, s.embedding, s.group_id, s.id
            FROM sentences s
            JOIN text_categories l ON s.id = l.sentence_id
            WHERE l.name = ?
        """
        query_params = [name]

        self.cursor.execute(sql_query, tuple(query_params))
        rows = self.cursor.fetchall()

        file_paths = {row["file_path"] for row in rows}

        results = {"sent_dicts": []}
        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and "embedding" in row:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            results["meta_properties"] = self._fetch_meta_properties(file_paths)  # type: ignore

        return results

    def get_sents_by_meta_property(
        self,
        label_name: str,
        name: str,
        value: Any | None = None,
        value_range: tuple | None = None,
        multiple_values: list[Any] | None = None,
        include_meta_properties: bool = True,
        include_embeddings: bool = False,
    ) -> dict[str, Any]:
        """Same return type as get_sents_by_folder.

        Must specify one and only one of: value, value_type, value_range.

        Args:
            name (str):
            value (Any | None, optional): Defaults to None.
            value_range (tuple | None, optional): Min and max values. Defaults
                to None.
            multiple_values (list[Any] | None, optional): Multiple values.
                Defaults to None.
            include_embeddings (bool, optional):  Defaults to True.

        Returns:
            list[dict[str, Any]]
        """
        query = """
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
            JOIN meta_properties l ON s.file_path = l.file_path
            WHERE l.label_name = ? AND l.name = ?
        """
        query_params = [label_name, name]

        # Handle value range for numeric labels
        if value_range:
            query += " AND CAST(l.value AS REAL) BETWEEN ? AND ?"
            query_params.extend(value_range)
        elif multiple_values:
            query += f" AND l.value IN ({','.join(['?']*len(multiple_values))})"
            query_params.extend(multiple_values)
        else:
            # Handle None value case
            if value is None:
                query += " AND l.value IS NULL"
            else:
                query += " AND l.value = ?"
                query_params.append(str(value))

        self.cursor.execute(query, tuple(query_params))
        rows = self.cursor.fetchall()

        file_paths = {row["file_path"] for row in rows}

        results = {"sent_dicts": []}

        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and "embedding" in row:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        if include_meta_properties:
            results["meta_properties"] = file_paths  # type: ignore

        return results

    def get_all_sents(
        self,
        include_embeddings: bool = False,
        include_meta_properties: bool = True,
        sents_only: bool = False,
    ) -> dict[str, Any] | list[str]:
        """
        Same args and return type as get_sents_by_folder unless sents_only is
        True.
        """
        query = """
            SELECT s.id, s.sentence, s.file_path, s.embedding, s.group_id
            FROM sentences s
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        results = {"sent_dicts": []}

        if sents_only:
            return [row["sentence"] for row in rows]

        if include_meta_properties:
            file_paths = {row["file_path"] for row in rows}
            results["meta_properties"] = self._fetch_meta_properties(file_paths)  # type: ignore

        for row in rows:
            sent_dict = self._fetch_sent_dict(
                row, include_embeddings=include_embeddings
            )

            if include_embeddings and row["embedding"]:
                sent_dict["embedding"] = self._deserialize_embedding(row["embedding"])

            results["sent_dicts"].append(sent_dict)

        return results

    def add_embeddings(self, embeddings: list[np.ndarray]) -> None:
        """
        Replaces all existing embeddings with the provided list of new
            embeddings.

        Args:
            embeddings (list of np.ndarray): The new embeddings to replace
                the current ones in the database.

        Raises:
            ValueError: If the number of embeddings does not match the number
                of sentences in the database.
        """
        # Ensure that the number of embeddings matches the number of sentences in the database
        self.cursor.execute("SELECT COUNT(*) FROM sentences")
        num_sentences = self.cursor.fetchone()[0]

        if len(embeddings) != num_sentences:
            raise ValueError(
                f"The number of embeddings ({len(embeddings)}) does not match the number of sentences ({num_sentences})."
            )

        # Update the embeddings for all sentences
        for i, embedding in enumerate(embeddings):
            embedding_blob = self._serialize_embedding(embedding)
            self.cursor.execute(
                """
                UPDATE sentences
                SET embedding = ?
                WHERE id = ?
                """,
                (embedding_blob, i + 1),  # Assuming the IDs are 1-based
            )

        self.connection.commit()

    def close(self):
        self.connection.close()
