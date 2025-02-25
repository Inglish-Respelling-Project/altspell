'''
    Altspell  Flask web app for translating traditional English to respelled
    English and vice versa
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

import uuid
from typing import List, Type
from flask import current_app
from sqlalchemy.exc import IntegrityError
from .repositories import TranslationRepository, SpellingSystemRepository
from .model import SpellingSystem, Translation
from .exceptions import (
    MissingKeyError, InvalidTypeError, EmptyTranslationError, SpellingSystemUnavailableError
)


class SpellingSystemService:
    """A service providing functionality for spelling system endpoints."""

    @staticmethod
    def get_spelling_systems() -> List[str]:
        """
        Returns:
            A List of active spelling systems.
        """
        return list(current_app.plugin_instances.keys())

class TranslationService:
    """A service providing functionality for translation endpoints."""

    def __init__(
        self,
        translation_repository: TranslationRepository,
        spelling_system_repository: SpellingSystemRepository
    ):
        self._translation_repository: TranslationRepository = translation_repository
        self._spelling_system_repository: SpellingSystemRepository = spelling_system_repository

    def get_translation_by_id(self, translation_id: uuid) -> Translation:
        """
        Retrieve a Translation by id, from the database.

        Args:
            translation_id (uuid): Id of the Translation to query.

        Returns:
            Translation: A Translation object representing the queried database record.
        """
        return self._translation_repository.get_by_id(translation_id)

    def add_spelling_system(self, spelling_system: str) -> SpellingSystem:
        """
        Add a spelling system to the database.

        Args:
            spelling_system (str): Name of the spelling system to add.

        Returns:
            SpellingSystem: A SpellingSystem object representing the added database record.
        """
        try:
            return self._spelling_system_repository.add(spelling_system)
        except IntegrityError:
            return self._spelling_system_repository.get_by_name(spelling_system)

    def translate(
        self,
        spelling_system: str,
        forward: bool,
        text: str,
        save: bool
    ) -> Translation:
        """
        Perform a translation, optionally saving it to the database.

        Args:
            spelling_system (str): Name of the spelling system to use for translation.
            forward (bool): True for translation to the alternative spelling system. False for \
                translation to traditional English spelling.
            text (str): Text to be translated.
            save (bool): If true, persist the translation to the database.

        Returns:
            Translation: A Translation object representing the added database record.
        """

        # assign default save value
        if save is None:
            save = False

        def validate_key(key, key_pascal_case: str, cls: Type):
            if key is None:
                raise MissingKeyError(key_pascal_case)

            if not isinstance(key, cls):
                raise InvalidTypeError(key_pascal_case, cls)

        # exception handling
        validate_key(spelling_system, "spellingSystem", str)
        validate_key(forward, "forward", bool)
        validate_key(text, "text", str)

        if text == '':
            raise EmptyTranslationError

        selected_spelling_system = current_app.plugin_instances.get(spelling_system)

        if selected_spelling_system is None:
            raise SpellingSystemUnavailableError(spelling_system)

        # raises SpellingSystemNotFoundError if not found
        spelling_system = self._spelling_system_repository.get_by_name(spelling_system)

        # get translation functions
        translate_to_respelling = selected_spelling_system.translate_to_respelling
        translate_to_traditional_spelling = \
            selected_spelling_system.translate_to_traditional_spelling

        translation_length_limit = current_app.config['TRANSLATION_LENGTH_LIMIT']

        text = text[:translation_length_limit]

        if forward:
            traditional_text = text

            # raises NotImplementedFwdError if unimplemented
            respelled_text = translate_to_respelling(text)
        else:
            # raises NotImplementedBwdError if unimplemented
            traditional_text = translate_to_traditional_spelling(text)

            respelled_text = text

        translation = Translation(
            forward=forward,
            traditional_text=traditional_text,
            respelled_text=respelled_text,
            spelling_system_id=spelling_system.id
        )

        translation.spelling_system = spelling_system

        if save:
            translation = self._translation_repository.add(
                forward=forward,
                traditional_text=traditional_text,
                respelled_text=respelled_text,
                spelling_system_id=spelling_system.id,
            )

        return translation
