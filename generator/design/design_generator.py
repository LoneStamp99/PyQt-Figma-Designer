"""
This module contains the abstract class DesignGenerator that is the base class for all design generators.
"""
from abc import abstractmethod
from typing import List, Iterator

import config


class DesignGenerator:
    """
    Abstract class for all design generators.
    """

    # used_names is a set of all the names that have been used by any design generator to avoid name conflicts.
    used_names: set = set()

    # The short class name is the name of the class without the 'Handler' / 'Controller' / ... suffix
    short_class_name: str
    # The parent design generator.
    parent: 'DesignGenerator|None' = None
    # The figma node that generated this design generator.
    figma_node: dict
    # The list of children design generators.
    children: List['DesignGenerator']
    # The name of the generated q widget.
    q_widget_name: str

    # The path to the handler class.
    handler_class_path: str = ''
    # The path to the controller class.
    controller_class_path: str = ''
    # The path to the strings class.
    strings_class_path: str = ''
    # The path to the config class.
    config_class_path: str = ''

    def __init__(self, figma_node: dict, parent: 'DesignGenerator|None'):
        """
        Create a new design generator.
        Args:
            figma_node: The figma node that generated this design generator.
            parent: The parent design generator.
        """
        self.figma_node = figma_node
        self.children = []
        self.q_widget_name = self.create_name(figma_node)
        self.short_class_name = self.q_widget_name.replace('_', ' ').title().replace(' ', '')
        if parent is not None:
            self.parent = parent
            self.parent.children.append(self)
            self.controller_class_path = parent.controller_class_path
            self.handler_class_path = parent.handler_class_path
            self.strings_class_path = parent.strings_class_path
            self.config_class_path = parent.config_class_path

    @property
    def bounds(self) -> (float, float, float, float):
        """
        Get the bounds of the generator relative to the parent.
        returns:
            A tuple of floats (x, y, width, height) representing the bounds of the generator relative to the parent.
        """
        parent_start_x, parent_start_y = 0, 0
        if self.parent is not None:
            parent_bounds = self.parent.figma_node.get('absoluteBoundingBox', {'x': 0, 'y': 0, 'width': 0, 'height': 0})
            parent_start_x, parent_start_y = parent_bounds['x'], parent_bounds['y']
        bounds = self.figma_node.get('absoluteBoundingBox', {'x': 0, 'y': 0, 'width': 0, 'height': 0})
        x, y = bounds['x'] - parent_start_x, bounds['y'] - parent_start_y
        width, height = bounds['width'], bounds['height']
        x, y, width, height = x * config.scale, y * config.scale, width * config.scale, height * config.scale
        return x, y, width, height

    @property
    def pyqt_bounds(self):
        """
        Get the bounds of the generator relative to the parent in the format of a QRect.
        returns:
            A string representing the bounds of the generator relative to the parent in the format of a QRect.
        """
        x, y, width, height = self.bounds
        return f'QRect({int(x)}, {int(y)}, {int(width)}, {int(height)})'

    @classmethod
    def create_name(cls, figma_node: dict) -> str:
        """
        Create a name for the given figma node. Ensure that the name is unique and valid.
        Args:
            figma_node: The figma node to create a name for.
        returns:
            A string representing the name of the given figma node.
        """
        view_name = figma_node['name'].replace(' ', '_').lower()
        view_name = ''.join(c for c in view_name if c.isalnum() or c == '_')
        while '__' in view_name:
            view_name = view_name.replace('__', '_')
        while view_name.startswith('_'):
            view_name = view_name[1:]
        while view_name.endswith('_'):
            view_name = view_name[:-1]
        if view_name == '':
            view_name = 'view'
        if view_name[0].isdigit():
            view_name = '_' + view_name
        i = 0
        new_name = view_name
        while new_name in cls.used_names:
            new_name = f'{view_name}_{i}'
            i += 1
        view_name = new_name
        cls.used_names.add(view_name)
        return view_name

    @abstractmethod
    def generate_design(self) -> Iterator[str]:
        """
        Generate the code to create the design of the generator. This code extends 'gui.py'.
        returns:
            An iterator of strings containing the code to reproduce the figma design into a python pyqt6 code.
        """
        pass

    def generate_handler(self) -> Iterator[str]:
        """
        Generate the code to create the handler of the generator. This code extends 'gui_handler.py'.
        You must call the generated handler functions in the generated design.
        returns:
            An iterator of strings containing the code to create the handler of the generator.
        """
        for child in self.children:
            yield from child.generate_handler()

    def generate_controller(self) -> Iterator[str]:
        """
        Generates the code to create the controller of the generator. This code extends 'gui_controller.py'.
        You must link the generated controller functions to your lambdas in the generated design.
        returns:
            An iterator of strings containing the code to create the controller of the generator.
        """
        for child in self.children:
            yield from child.generate_controller()

    def generate_strings(self) -> Iterator[str]:
        """
        Generates the code to create the strings of the generator. This code extends 'strings.py'.
        You must use the generated strings in the generated design.
        returns:
            An iterator of strings containing the code to create the strings of the generator.
        """
        for child in self.children:
            yield from child.generate_strings()

    def generate_config(self) -> Iterator[str]:
        """
        Generates the code to create the config of the generator. This code extends 'components_config.py'.
        You must use the generated config in the generated design.
        returns:
            An iterator of strings containing the code to create the config of the generator.
        """
        for child in self.children:
            yield from child.generate_config()
