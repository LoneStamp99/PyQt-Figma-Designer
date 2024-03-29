"""
This module contains the class TextGenerator that is used to generate every text in the design.
"""
from typing import Iterator

import config
from generator.design.design_generator import DesignGenerator
from generator.utils import generate_controller_setup, generate_print, generate_controller_function


class TextGenerator(DesignGenerator):
    """
    Class used to generate every text in the design.
    """
    # The name of the function used to set the text of the text in the GuiController.
    controller_set_text_function_name: str

    @property
    def string(self):
        """
        Get the content of the text.
        returns:
            The content of the text.
        """
        return self.figma_node['characters'].replace('"', '\\"').replace('\n', '\\n')

    @property
    def string_name(self):
        """
        Get the name of the string variable.
        returns:
            The name of the string variable.
        """
        return f'text_{self.q_widget_name}'.upper()

    def generate_design(self):
        """
        Generates a PyQt QLabel.
        returns:
            An iterator of strings containing the code to generate a PyQt QLabel.
        """
        self.controller_set_text_function_name = f'{self.q_widget_name}_set_text'

        font = self.figma_node['style']['fontFamily']
        font_size = self.figma_node['style']['fontSize'] * config.text_scale * config.scale
        color = 'rgba(0, 0, 0, 0)'
        if len(self.figma_node['fills']) > 0 and 'color' in self.figma_node['fills'][0]:
            color = self.figma_node['fills'][0]['color']
            color = f'rgba({color["r"] * 255}, {color["g"] * 255}, {color["b"] * 255}, {color.get("a", 1) * 255})'

        vertical_alignment_figma = self.figma_node['style']['textAlignVertical']
        horizontal_alignment_figma = self.figma_node['style']['textAlignHorizontal']
        match vertical_alignment_figma:
            case 'TOP':
                vertical_alignment = 'Qt.AlignTop'
            case 'BOTTOM':
                vertical_alignment = 'Qt.AlignBottom'
            case 'CENTER':
                vertical_alignment = 'Qt.AlignVCenter'
            case _:
                vertical_alignment = 'Qt.AlignVCenter'
        match horizontal_alignment_figma:
            case 'LEFT':
                horizontal_alignment = 'Qt.AlignLeft'
            case 'RIGHT':
                horizontal_alignment = 'Qt.AlignRight'
            case 'CENTER':
                horizontal_alignment = 'Qt.AlignHCenter'
            case 'JUSTIFIED':
                horizontal_alignment = 'Qt.AlignJustify'
            case _:
                horizontal_alignment = 'Qt.AlignHCenter'

        yield from f"""self.{self.q_widget_name} = QLabel(self.{self.parent.q_widget_name})
self.{self.q_widget_name}.setText({self.strings_class_path}.{self.string_name})
font = QFont()
font.setFamilies([u"{font}"])
font.setPointSize({int(font_size)})
self.{self.q_widget_name}.setFont(font)
self.{self.q_widget_name}.setStyleSheet("color: {color}")
self.{self.q_widget_name}.setGeometry({self.pyqt_bounds})
self.{self.q_widget_name}.setAlignment({vertical_alignment} | {horizontal_alignment})
self.{self.q_widget_name}.setMouseTracking(False)
self.{self.q_widget_name}.setContextMenuPolicy(Qt.NoContextMenu)
self.{self.q_widget_name}.setWordWrap(True)
def {self.controller_set_text_function_name}(text:str):
    self.{self.q_widget_name}.setText(text)""".splitlines()
        yield from generate_controller_setup(self, self.controller_set_text_function_name,
                                             self.controller_set_text_function_name)

    def generate_controller(self):
        """
        Generates the function used to set the text of the text in the GuiController.
        returns:
            An iterator of strings containing the code to generate the function used to set the text of the text in the GuiController.
        """
        yield from generate_controller_function(self.controller_set_text_function_name, 'text:str')

    def generate_strings(self) -> Iterator[str]:
        __doc__ = super().generate_strings().__doc__
        yield f'{self.string_name} = \'{self.string}\''
