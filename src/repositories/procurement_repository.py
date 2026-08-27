from datetime import datetime, timezone
from enum import Enum
from sqlite3 import Row
from typing import Optional

from src.database.connection import get_connection
from src.models.procurement import Procurement


class SaveStatus(str, Enum):
    INSERTED = "inserted"
    UPDATED = "updated"
    DUPLICATE = "duplicate"


class ProcurementRepository:
    def find_by_pncp_id(self, pncp_id: str) -> Optional[Row]:
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM procurements
                WHERE pncp_id = ?
                """,
                (pncp_id,),
            )

            return cursor.fetchone()

        finally:
            connection.close()

    def _build_filters(
        self,
        state: Optional[str] = None,
        modality: Optional[str] = None,
        organization: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[str, list]:
        """
        Monta os filtros utilizados nas consultas da API,
        mantendo os valores como parâmetros SQL.
        """

        clauses = []
        parameters = []

        if state:
            state = state.strip()

            if state:
                clauses.append(
                    "UPPER(state) = UPPER(?)"
                )
                parameters.append(state)

        if modality:
            modality = modality.strip()

            if modality:
                clauses.append(
                    "LOWER(modality) LIKE LOWER(?)"
                )
                parameters.append(
                    f"%{modality}%"
                )

        if organization:
            organization = organization.strip()

            if organization:
                clauses.append(
                    "LOWER(organization) LIKE LOWER(?)"
                )
                parameters.append(
                    f"%{organization}%"
                )

        if search:
            search = search.strip()

            if search:
                search_value = f"%{search}%"

                clauses.append(
                    """
                    (
                        LOWER(title) LIKE LOWER(?)
                        OR LOWER(object_description) LIKE LOWER(?)
                        OR LOWER(organization) LIKE LOWER(?)
                    )
                    """
                )

                parameters.extend(
                    [
                        search_value,
                        search_value,
                        search_value,
                    ]
                )

        if not clauses:
            return "", parameters

        where_clause = (
            " WHERE "
            + " AND ".join(clauses)
        )

        return where_clause, parameters

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        state: Optional[str] = None,
        modality: Optional[str] = None,
        organization: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Row]:
        """Retorna registros paginados com filtros opcionais."""

        where_clause, parameters = self._build_filters(
            state=state,
            modality=modality,
            organization=organization,
            search=search,
        )

        query = (
            """
            SELECT
                pncp_id,
                title,
                modality,
                last_update,
                organization,
                city,
                state,
                object_description,
                url,
                first_seen_at,
                last_seen_at,
                updated_at
            FROM procurements
            """
            + where_clause
            + """
            ORDER BY
                last_update DESC,
                pncp_id ASC
            LIMIT ?
            OFFSET ?
            """
        )

        parameters.extend(
            [
                limit,
                offset,
            ]
        )

        connection = get_connection()

        try:
            cursor = connection.execute(
                query,
                parameters,
            )

            return cursor.fetchall()

        finally:
            connection.close()

    def count_filtered(
        self,
        state: Optional[str] = None,
        modality: Optional[str] = None,
        organization: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        where_clause, parameters = self._build_filters(
            state=state,
            modality=modality,
            organization=organization,
            search=search,
        )

        query = (
            """
            SELECT COUNT(*) AS total
            FROM procurements
            """
            + where_clause
        )

        connection = get_connection()

        try:
            cursor = connection.execute(
                query,
                parameters,
            )

            row = cursor.fetchone()

            return row["total"]

        finally:
            connection.close()

    def _has_changes(
        self,
        existing: Row,
        procurement: Procurement,
    ) -> bool:
        """Verifica se o registro coletado difere do armazenado."""

        last_update = (
            procurement.last_update.isoformat()
            if procurement.last_update
            else None
        )

        comparisons = {
            "title": procurement.title,
            "modality": procurement.modality,
            "last_update": last_update,
            "organization": procurement.organization,
            "city": procurement.city,
            "state": procurement.state,
            "object_description": procurement.object_description,
            "url": procurement.url,
        }

        for field, new_value in comparisons.items():
            if existing[field] != new_value:
                return True

        return False

    def save(
        self,
        procurement: Procurement,
    ) -> SaveStatus:
        """
        Insere novos registros, atualiza registros alterados
        e identifica registros já existentes sem alteração.
        """

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM procurements
                WHERE pncp_id = ?
                """,
                (procurement.pncp_id,),
            )

            existing = cursor.fetchone()

            now = datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )

            last_update = (
                procurement.last_update.isoformat()
                if procurement.last_update
                else None
            )

            if existing is None:
                connection.execute(
                    """
                    INSERT INTO procurements (
                        pncp_id,
                        title,
                        modality,
                        last_update,
                        organization,
                        city,
                        state,
                        object_description,
                        url,
                        first_seen_at,
                        last_seen_at,
                        updated_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        procurement.pncp_id,
                        procurement.title,
                        procurement.modality,
                        last_update,
                        procurement.organization,
                        procurement.city,
                        procurement.state,
                        procurement.object_description,
                        procurement.url,
                        now,
                        now,
                        now,
                    ),
                )

                connection.commit()

                return SaveStatus.INSERTED

            if not self._has_changes(
                existing,
                procurement,
            ):
                connection.execute(
                    """
                    UPDATE procurements
                    SET last_seen_at = ?
                    WHERE pncp_id = ?
                    """,
                    (
                        now,
                        procurement.pncp_id,
                    ),
                )

                connection.commit()

                return SaveStatus.DUPLICATE

            connection.execute(
                """
                UPDATE procurements
                SET
                    title = ?,
                    modality = ?,
                    last_update = ?,
                    organization = ?,
                    city = ?,
                    state = ?,
                    object_description = ?,
                    url = ?,
                    last_seen_at = ?,
                    updated_at = ?
                WHERE pncp_id = ?
                """,
                (
                    procurement.title,
                    procurement.modality,
                    last_update,
                    procurement.organization,
                    procurement.city,
                    procurement.state,
                    procurement.object_description,
                    procurement.url,
                    now,
                    now,
                    procurement.pncp_id,
                ),
            )

            connection.commit()

            return SaveStatus.UPDATED

        finally:
            connection.close()

    def count(self) -> int:
        """Retorna a quantidade total de contratações armazenadas."""

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM procurements
                """
            )

            row = cursor.fetchone()

            return row["total"]

        finally:
            connection.close()