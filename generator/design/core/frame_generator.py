"""
This module contains FrameGenerator class responsible for generating
 a pyqt6 window corresponding to a figma root-level frame.
"""
from typing import Iterator

import config
from generator.utils import indent, generate_handler_call

from generator.design.design_generator import DesignGenerator


class FrameGenerator(DesignGenerator):
    """
    Responsible for generating a pyqt6 window corresponding to a figma root-level frame.
    """
    short_class_name: str
    window_class_name: str

    windows = {}  # node id -> window name

    def __init__(self, figma_node, parent=None):
        super().__init__(figma_node, parent)
        self.window_class_name = f'QWindow{self.short_class_name}'
        FrameGenerator.windows[self.figma_node['id']] = self.window_class_name

    def generate_design(self) -> Iterator[str]:
        """
        Generates a PyQt6 window (and its children).
        returns:
            An iterator of strings containing the code to generate a PyQt6 window.
        """
        # import it here to avoid circular import
        from generator.design.core.factory_generator import FactoryGenerator
        bounds = self.figma_node['absoluteBoundingBox']
        width, height = bounds['width'], bounds['height']
        self.handler_class_path = f'{self.handler_class_path}.{self.short_class_name}Handler'
        self.controller_class_path = f'{self.controller_class_path}.{self.short_class_name}Controller'
        self.strings_class_path = f'{self.strings_class_path}.{self.short_class_name}Strings'
        self.config_class_path = f'{self.config_class_path}.{self.short_class_name}Config'
        yield from f"""


class {self.window_class_name}(object):
    is_singleton_open = False
    def setupUi(self, MainWindow):
        if not {self.window_class_name}.is_singleton_open:
            {self.window_class_name}.is_singleton_open = True
        else:
            raise Exception('Only one instance of {self.window_class_name} can be opened at a time')
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        self.MainWindow = MainWindow
        MainWindow.resize({width * config.scale}, {height * config.scale})
        self.{self.q_widget_name} = QWidget(MainWindow)        
        MainWindow.setFixedSize({width * config.scale}, {height * config.scale})
        MainWindow.setWindowTitle("{self.figma_node['name']}")""".splitlines()
        yield from indent(FactoryGenerator(self.figma_node, self).generate_design(), n=2)
        yield from indent(f'MainWindow.setCentralWidget(self.{self.q_widget_name})', n=2)
        yield from indent(generate_handler_call(self, 'window_started'), n=2)
        yield from indent('def __window_closed(*args, **kwargs):', n=2)
        yield from indent(generate_handler_call(self, 'window_closed'), n=3)
        yield from indent(f'{self.window_class_name}.is_singleton_open = False', n=3)
        yield from indent('MainWindow.closeEvent = __window_closed', n=2)

    def generate_handler(self) -> Iterator[str]:
        __doc__ = super().generate_handler().__doc__
        yield from f"""

class {self.handler_class_path.split(".")[-1]}:

    @classmethod
    def window_started(cls):
        pass
        
    @classmethod
    def window_closed(cls):
        pass""".splitlines()
        yield from indent(super().generate_handler())

    def generate_controller(self) -> Iterator[str]:
        __doc__ = super().generate_controller().__doc__
        sub_controllers = list(indent(super().generate_controller()))
        if len(sub_controllers) == 0:
            return [].__iter__()
        yield f'class {self.controller_class_path.split(".")[-1]}:'
        yield from sub_controllers

    def generate_strings(self) -> Iterator[str]:
        __doc__ = super().generate_strings().__doc__
        sub_strings = list(indent(super().generate_strings()))
        if len(sub_strings) == 0:
            return [].__iter__()
        yield f'class {self.strings_class_path.split(".")[-1]}:'
        yield from sub_strings

    def generate_config(self) -> Iterator[str]:
        __doc__ = super().generate_config().__doc__
        sub_config = list(indent(super().generate_config()))
        if len(sub_config) == 0:
            return [].__iter__()
        yield f'class {self.config_class_path.split(".")[-1]}:'
        yield from sub_config

    @classmethod
    def get_window_name(cls, node_id):
        return cls.windows.get(node_id, None)
