"""Base classes for handling all BRER metadata.

State and PairData classes derive from this module.
"""

import json
import sys
import warnings
from typing import Collection
from typing import Mapping
from typing import Optional

if sys.version_info.major > 3 or sys.version_info.minor >= 9:
    List = list
else:
    from typing import List


class MetaData:
    def __init__(self, name: str, required_parameters: Collection[str] = ()):
        """Construct metadata object and give it a name.

        Parameters
        ----------
        name :
            Give your MetaData class a descriptive name.
        required_parameters :
            The names of the required parameters for this data collection.
        """
        self.__name = name
        self.__required_parameters = tuple(required_parameters)
        self._metadata = {}

    @property
    def name(self):
        """Name that associates the class with a pair or a particular function
        (such as with the Plugins, which are named either 'training',
        'convergence' or 'production').

        Returns
        -------
        str
            the name of the class
        """
        return self.__name

    @name.setter
    def name(self, name):
        """setter for name.

        Parameters
        ----------
        name : str
            name of the class
        """
        self.__name = name

    def get_requirements(self):
        """Gets the set of required parameters for the class. This is quite
        useful for checking if there are any missing parameters before
        beginning a run.

        Returns
        -------
        list
            required parameters of the class
        """
        return self.__required_parameters

    def set(self, key=None, value=None, **kwargs):
        """Sets one or more parameters of the class.

        Parameters may be provided with the *key* and *value* arguments, or as
        any number of keyword arguments.

        Checks whether parameters are required and reports information about
        requirements.

        Parameters
        ----------
        key : str, optional
            parameter name, by default None
        value : any, optional
            parameter value, by default None
        """
        if key is not None or value is not None:
            if key is None or value is None:
                raise TypeError('Both *key* and *value* must be provided, if either is used.')
        kwargs[key] = value
        for key, value in kwargs.items():
            if key not in self.__required_parameters and key != "name":
                warnings.warn(
                    f"{key} is not a required parameter of {self.name}: setting anyway")
            self._metadata[key] = value

    def get(self, key):
        """Get the value of a parameter of the class.

        Parameters
        ----------
        key : str
            The name of the parameter you wish to get.

        Returns
        -------
            The value of the parameter associated with the key.
        """
        return self._metadata[key]

    def set_from_dictionary(self, data: Mapping):
        """Another method that essentially performs the same thing as "set",
        but just takes a dictionary. Probably should be deprecated...

        Parameters
        ----------
        data : dict
            A dictionary of parameter names and values to set.
        """
        self.set(**data)

    def get_as_dictionary(self):
        """Get all of the current parameters of the class as a dictionary.

        Returns
        -------
        dict
            dictionary of class parameters
        """
        return self._metadata

    def get_missing_keys(self):
        """Gets all of the required parameters that have not been set.

        Returns
        -------
        list
            A list of required parameter names that have not been set.
        """
        missing = []
        for required in self.__required_parameters:
            if required not in self._metadata.keys():
                missing.append(required)
        return missing


class MultiMetaData:
    """A collection of MetaData instances.

    A useful data structure when restraining multiple atom-atom pairs.
    """

    def __init__(self, metadata: Optional[List[MetaData]] = None):
        self._metadata_list: List[MetaData] = []

    @property
    def names(self):
        """A list of named metadata collections.

        Names associate each class with a pair or a particular function
        (such as with the Plugins, which are named either 'training',
        'convergence' or 'production').
        """
        if not self._metadata_list:
            raise AttributeError('Must import a list of metadata before retrieving names')
        return [metadata.name for metadata in self._metadata_list]

    def add_metadata(self, metadata: MetaData):
        """Appends new MetaData object to self._metadata.

        Parameters
        ----------
        metadata : MetaData
            metadata to append
        """
        self._metadata_list.append(metadata)

    def name_to_id(self, name):
        """Converts the name of one of the MetaData classes to it's associated
        list index (it's idx in self._metadata)

        Parameters
        ----------
        name : str
            the name of a MetaData class.

        Returns
        -------
        int
            the index of the MetaData class in the self._metadata list.

        Raises
        ------
        IndexError
            Raise IndexError if no metadata have been loaded.
        """
        names = self.names
        if name not in names:
            raise IndexError('{} is not a valid name.'.format(name))
        return names.index(name)

    def id_to_name(self, id):
        """Converts the index of one of the MetaData classes to it's associated
        name.

        Parameters
        ----------
        id : int
            The index of the MetaData class in the list self._metadata

        Returns
        -------
        str
            the name of the metadata class
        """
        return self.names[id]

    def __getitem__(self, item):
        return self._metadata_list[item]

    def get_as_single_dataset(self):
        """"""
        single_dataset = {}
        for metadata in self._metadata_list:
            single_dataset[metadata.name] = metadata.get_as_dictionary()
        return single_dataset

    def write_to_json(self, filename='state.json'):
        """Writes state to json.

        Parameters
        ----------
        filename : str
             (Default value = 'state.json')
        """
        with open(filename, 'w') as fh:
            json.dump(self.get_as_single_dataset(), fh)

    @classmethod
    def from_json(cls, filename='state.json'):
        """Reads state from json.

        Parameters
        ----------
        filename : str
             (Default value = 'state.json')
        """
        with open(filename, 'r') as fh:
            data = json.load(fh)
        for name, metadata in data.items():
            metadata_obj = MetaData(name=name)
            metadata_obj.set_from_dictionary(metadata)
            self._metadata_list.append(metadata_obj)
