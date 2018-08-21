"""
Abstract class for handling all BRER metadata. State and PairData classes inherit from this class.
"""
from abc import ABC, abstractmethod
import json


class MetaData(ABC):

    def __init__(self, name):
        """
        Construct metadata object and give it a name
        :param name:
        """
        self.__name = name
        self.__required_parameters = []
        self._metadata = {}

    @property
    def name(self):
        return self.__name

    @name.getter
    def name(self):
        return self.__name

    def set_requirements(self, list_of_requirements: list):
        self.__required_parameters = list_of_requirements

    def get_requirements(self):
        return self.__required_parameters

    def set(self, key, value):
        self._metadata[key] = value

    def get(self, key):
        return self._metadata[key]

    def set_from_dictionary(self, data):
        self._metadata = data

    def get_dictionary(self):
        return self._metadata

    def get_missing_keys(self):
        missing = []
        for required in self.__required_parameters:
            if required not in self._metadata.keys():
                missing.append(required)
        return missing


class MultiMetaData(ABC):

    def __init__(self):
        self._data = {}

    def ingest_data(self, list_metadata):
        for metadata in list_metadata:
            name = metadata.__getattribute__('name')
            self._data[name] = metadata.get_dictionary()

    def get(self, name, key):
        return self._data[name][key]

    def get_names(self):
        return list(self._data.keys())

    def get_single_dataset(self, name):
        return self._data[name]

    def write_to_json(self, filename='state.json'):
        json.dump(self._data, open(filename, 'w'))

    def read_from_json(self, filename='state.json'):
        self._data = json.load(open(filename, 'r'))
