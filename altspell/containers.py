'''
    Altspell  Flask web app for converting traditional English spelling to
    an alternative spelling
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

from dependency_injector import containers, providers
from flask import current_app
from .services import PluginService, ConversionService
from .repositories import AltspellingRepository, ConversionRepository
from .database import Database


class Container(containers.DeclarativeContainer):
    """Container for injecting dependencies into blueprint modules."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            ".blueprints.plugin", 
            ".blueprints.conversion",
            ".utils.populate_altspelling_table"
        ]
    )

    db = providers.Singleton(Database, db_url=current_app.config["SQLALCHEMY_DATABASE_URI"])

    plugin_service = providers.Factory(
        PluginService
    )

    altspelling_repository = providers.Singleton(
        AltspellingRepository,
        session_factory=db.provided.session
    )

    conversion_repository = providers.Singleton(
        ConversionRepository,
        session_factory=db.provided.session
    )

    conversion_service = providers.Factory(
        ConversionService,
        conversion_repository=conversion_repository,
        altspelling_repository=altspelling_repository
    )
