import csv
import logging
import os
import threading
import time
import traceback
import uuid

from django.conf import settings

import logger
import xlrd
from cassandra.cqlengine.query import DoesNotExist
from cassandra.cqlengine.query import LWTException
from category.models import *
from es_manager.category import CategoryIndexer
from es_manager.category import CategorySearcher
from slugify import SLUG_OK
from slugify import slugify
from system.analyser import ListAsTags
from system.exceptions import CategoryConstraintException
from system.exceptions import CategoryException
from system.exceptions import CustomFiledException
from system.paginator import Paginator
from system.response import *
from system.vars import BASE_PRICING
from system.vars import CategoryTranslationFlag
from system.vars import Operator
from system.xml_serializer import XmlFileDeserializer
from system.xml_serializer import XmlSerializer


controller_logger = logger.get_logger(__file__)

# Globals
xml_semaphore = threading.BoundedSemaphore()
"Requis pour l'import/export XML asynchrone"


class CustomFieldController(object):
    """Controleur de champs personalisés (Déprécié)

    :param field_name: nom du champ à créer/mettre à jour
    """

    field_name = None

    def __init__(self, **kwargs):
        self.field_name = kwargs.get("field_name", None)

    def create_custom_field(self, field_name=None, **fields):
        """Création d'un champ personalisé

        :param field_name: nom du champ à créer
        :param fields: données du champ personalisé
        :type field_name: str
        :type fields: dict(CustomField)
        :return: objet champ personalisé
        :rtype: CustomField
        """
        if field_name:
            self.field_name = field_name

        try:
            CustomField.if_not_exists().create(field_name=self.field_name, **fields)
            cf = CustomField.objects().get(field_name=self.field_name)

        except LWTException:
            raise CustomFiledException(
                code=100,
                message="Custom field already exists",
                parameter=self.field_name,
            )

        return cf

    def update_custom_field(self, field_name=None, **fields):
        """Mise à jour d'un champ personalisé

        :param field_name: nom du champ à mettre à jour
        :param fields: données du champ personalisé
        :type field_name: str
        :type fields: dict(CustomField)
        :return: objet champ personalisé
        :rtype: CustomField
        """
        if field_name:
            self.field_name = field_name

        try:
            CustomField.objects(field_name=self.field_name).if_exists().update(**fields)
            cf = CustomField.objects().get(field_name=self.field_name)

        except LWTException:
            raise CustomFiledException(
                code=100,
                message="Custom field does not exists",
                parameter=self.field_name,
            )

        return cf

    def archive(self, field_name=None):
        """Archivage d'un champ personalisé

        :param field_name: nom du champ à mettre à jour
        :type field_name: str
        :return: None
        """
        if field_name:
            self.field_name = field_name
        CustomField.objects(field_name=self.field_name).update(archived=True)

    def get_custom_field(self, field_name=None):
        """Récupère l'objet champ personalisé correspondant dans la base de données

        :param field_name: nom du champ à récupérer
        :type field_name: str
        :return: objet champ personalisé
        :rtype: CustomField
        """
        if field_name:
            self.field_name = field_name
        cf = CustomField.objects().get(field_name=self.field_name)

        return cf

    def fetch_custom_field(self, field_names=None):
        """Récupère les champs cités dans la liste

        :param field_names: liste de noms de champs
        :type field_names: list(str)
        :return: Liste de champs personalisés
        :rtype: list(CustomField)
        """

        cfs = CustomField.objects(field_name__in=field_names).all()

        return cfs

    def list(self):
        """Renvoie tous les champs personalisés

        :return: Liste de champs personalisés
        :rtype: list(CustomField)
        """
        cfs = CustomField.objects().all()
        return cfs


class DataTemplateController(object):
    """Controleur de modèle de données (Déprécié)

    :param data_template_key: Nom du modèle de données
    :type data_template_key: str
    """

    def __init__(self, data_template_key=None):
        self.data_template_key = data_template_key

    def create(self, data_template_key=None, fields=None):
        """Crée un modèle de données personalisé

        :param data_template_key: Nom du modèle de données
        :param fields: données du modèle de données personalisé
        :type fields: dict(DataTemplate)
        :type data_template_key: str
        :return: Objet modèle de données
        :rtype: DataTemplate
        """
        if data_template_key:
            self.data_template_key = data_template_key

        # Vérifie l'existence du champ personalisé
        if "custom_fields" in fields:
            for cf in fields["custom_fields"]:
                CustomFieldController().get_custom_field(field_name=cf)

        # Création
        DataTemplate.create(data_template_key=data_template_key, **fields)

        return self.get(data_template_key=data_template_key)

    def update(self, data_template_key=None, fields=None):
        """Mise à jour modèle de données personalisé

        :param data_template_key: Nom du modèle de données
        :param fields: données du modèle de données personalisé
        :type fields: dict(DataTemplate)
        :type data_template_key: str
        :return: Objet modèle de données
        :rtype: DataTemplate
        """
        controlled_fields = [
            "custom_fields",
            "custom_fields__add",
            "custom_fields__remove",
        ]

        # Paramètre obligatoire
        if data_template_key:
            self.data_template_key = data_template_key

        # Controle des champs
        for controlled_field in controlled_fields:
            if controlled_field in fields:
                for cf in fields[controlled_field]:
                    CustomFieldController().get_custom_field(field_name=cf)

        # Mise à jour
        DataTemplate.objects(data_template_key=data_template_key).if_exists().update(
            **fields
        )

        return self.get(data_template_key=data_template_key)

    def get(self, data_template_key=None):
        """Récupère le modèle données correspondant à la clé

        :param data_template_key: Nom du modèle de données
        :type data_template_key: str
        :return: Objet modèle de données
        :rtype: DataTemplate
        """
        if data_template_key:
            self.data_template_key = data_template_key

        return DataTemplate.get(data_template_key=data_template_key)

    def delete(self, data_template_key=None):
        """Supression du modèle de données

        :param data_template_key: Nom du modèle de données
        :type data_template_key: str
        :return: None
        """
        if data_template_key:
            self.data_template_key = data_template_key

        self.get().delete()

    def if_exists(self, data_template_key=None):
        """Vérifie l'existence du modèle de données

        :param data_template_key: Nom du modèle de données
        :type data_template_key: str
        :return: Vrai si exisitant
        :rtype: bool
        """
        if data_template_key:
            self.data_template_key = data_template_key

        return (
            len(
                DataTemplate.objects().filter(
                    data_template_key__in=self.data_template_key
                )
            )
            == 1
        )

    def list(self):
        """Renvoie tous les modèles de données personalisés

        :return: Liste des objets de modèle de données personalisés
        :rtype: list(DataTemplate)
        """

        return DataTemplate.objects().all()
