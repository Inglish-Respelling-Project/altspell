'''
    Altspell  Flask web app for translating traditional English spelling to an alternative spelling
    Copyright (C) 2025  Nicholas Johnson

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from contextlib import AbstractAsyncContextManager
from typing import Callable
import uuid
from sqlalchemy.orm import Session, selectinload
from .model import Altspelling, Translation
from .exceptions import TranslationNotFoundError, AltspellingNotFoundError


class TranslationRepository:
    """Repository for database operations related to translations."""
    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractAsyncContextManager[Session]
        ]
    ) -> None:
        self.session_factory = session_factory

    def add(
        self,
        to_altspell: bool,
        tradspell_text: str,
        altspell_text: str,
        altspelling_id: int
    ) -> Translation:
        """
        Add a translation to the database.

        Args:
            to_altspell (bool): True if translated to the alternative spelling system. False if \
                translated to traditional English spelling.
            tradspell_text (str): Text in traditional English spelling.
            altspell_text (str): Text in the alternative English spelling system.
            altspelling_id (int): Id of the alternative spelling system.

        Returns:
            Translation: The translation object added to the database.
        """
        with self.session_factory() as session:
            translation = Translation(
                id=uuid.uuid4(),
                to_altspell=to_altspell,
                tradspell_text=tradspell_text,
                altspell_text=altspell_text,
                altspelling_id=altspelling_id
            )
            session.add(translation)
            session.commit()
            translation_with_altspelling = (
                session.query(Translation)
                .options(selectinload(Translation.altspelling))
                .filter(Translation.id == translation.id)
                .first()
            )
            return translation_with_altspelling

    def get_by_id(self, translation_id: uuid) -> Translation:
        """
        Retrieve a translation by id.

        Args:
            translation_id (uuid): Id of the requested translation.

        Returns:
            Translation: The translation object corresponding to translation_id.
        """
        with self.session_factory() as session:
            translation = (
                session.query(Translation)
                .options(selectinload(Translation.altspelling))
                .filter(Translation.id == translation_id)
                .first()
            )
            if not translation:
                raise TranslationNotFoundError(translation_id)
            return translation

class AltspellingRepository:
    """Repository for database operations related to alternative spelling systems."""
    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractAsyncContextManager[Session]
        ]
    ) -> None:
        self.session_factory = session_factory

    def add(self, altspelling_name: str) -> Altspelling:
        """
        Add an alternative spelling system.

        Args:
            altspelling_name (str): Name of the alternative spelling system.

        Returns:
            Altspelling: The alternative spelling system object added to the database.
        """
        with self.session_factory() as session:
            altspelling = Altspelling(name=altspelling_name)
            session.add(altspelling)
            session.commit()
            session.refresh(altspelling)
            return altspelling

    def get_all(self):
        """Retrieve a list of enabled alternative spelling systems."""
        with self.session_factory() as session:
            return session.query(Altspelling).all()

    def get_by_name(self, altspelling_name: str) -> Altspelling:
        """
        Retrieve an alternative spelling system object by alternative spelling system name.

        Args:
            altspelling_name (str): Name of the alternative spelling system.

        Returns:
            Altspelling: The alternative spelling system object corresponding to altspelling_name.
        """
        with self.session_factory() as session:
            altspelling = (
                session.query(Altspelling)
                .filter(Altspelling.name == altspelling_name)
                .first()
            )
            if not altspelling:
                raise AltspellingNotFoundError
            return altspelling
