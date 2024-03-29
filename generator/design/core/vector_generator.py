"""
This module contains the class VectorGenerator that is used to generate every vector in the design. (Images, Shapes, ...)
"""
from typing import Iterator

import config
from generator.design.design_generator import DesignGenerator
from generator.utils import logging


class SvgGenerator:
    """
    Class used to write svg files from figma geometry.
    """
    # The counter used to generate unique ids for the svg files.
    graphic_counter: int = 0

    @classmethod
    def create_svg_file(cls, figma_node: dict, filename: str):
        """
        Create a svg file from the figma node.
        Args:
            figma_node: The figma node that contains the fills and the strokes to be written in the svg file.
            filename: The name of the svg file.
        """
        bounds = f'0 0 {int(figma_node["absoluteBoundingBox"]["width"])} {int(figma_node["absoluteBoundingBox"]["height"])}'
        svg_file_data = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.2" baseProfile="tiny"  xmlns="http://www.w3.org/2000/svg">"""
        for i, (geometry, fill) in enumerate(
                zip(figma_node.get('fillGeometry', []), figma_node.get('fills', []))):
            for line in cls.generate_path(figma_node, geometry['path'], fill):
                svg_file_data += '\n\t' + line

        for i, (geometry, stroke) in enumerate(
                zip(figma_node.get('strokeGeometry', []), figma_node.get('strokes', []))):
            for line in cls.generate_path(figma_node, geometry['path'], stroke):
                svg_file_data += '\n\t' + line

        svg_file_data += '\n</svg>'
        with open(f'{config.svg_directory}/{filename}', 'w') as file:
            file.write(svg_file_data)

    @classmethod
    def generate_path(cls, figma_node: dict, path_data: str, graphic: dict) -> Iterator[str]:
        """
        Generate the svg path from the figma node.
        Args:
            figma_node: The figma node that contains the fills and the strokes to be written in the svg file.
            path_data: The path data of the svg path.
            graphic: The graphic that contains the fill or the stroke.
        returns:
            An iterator of strings representing the svg path.
        """
        cls.graphic_counter += 1
        stroke_width = figma_node.get('strokeWeight', 0)
        opacity = graphic.get('opacity', 1)

        match graphic['type']:
            case 'SOLID':
                color = graphic['color']
                opacity *= color.get('a', 0)
                color = color['r'], color['g'], color['b']
                color = '#{:02x}{:02x}{:02x}'.format(*map(lambda x: int(x * 255), color))
                yield (f'<path '
                       f'fill="{color}" stroke-width="{stroke_width}" '
                       f'fill-opacity="{opacity}" stroke-opacity="{opacity}" '
                       f'd="{path_data}"/>')
            case 'IMAGE':
                image_ref = graphic['imageRef']
                image = f'../images/{image_ref}.png'
                width, height = figma_node['absoluteBoundingBox']['width'], figma_node['absoluteBoundingBox'][
                    'height']
                img_ref = f'img{cls.graphic_counter}'
                yield f'<image x="0" y="0" width="{width}" height="{height}" xlink:href="{image}" id="{img_ref}" opacity="{opacity}"/>'
            case 'GRADIENT_LINEAR':
                gradient = graphic['gradientHandlePositions']
                gradient = f'x1="{gradient[0]["x"]}" y1="{gradient[0]["y"]}" x2="{gradient[1]["x"]}" y2="{gradient[1]["y"]}"'
                stops = graphic['gradientStops']
                yield f'<linearGradient id="gradient{cls.graphic_counter}" {gradient}>'
                for stop in stops:
                    color = stop['color']
                    stop_opacity = opacity * color.get('a', 1)
                    color = color['r'], color['g'], color['b']
                    color = '#{:02x}{:02x}{:02x}'.format(*map(lambda x: int(x * 255), color))
                    yield f'\t<stop offset="{stop["position"]}" stop-color="{color}" stop-opacity="{stop_opacity}"/>'
                yield f'</linearGradient>'
                yield f'<path fill="url(#gradient{cls.graphic_counter})" stroke-width="{stroke_width}" fill-opacity="{opacity}" stroke-opacity="{opacity}" d="{path_data}"/>'
            case 'GRADIENT_RADIAL':
                gradient = graphic['gradientHandlePositions']
                p0, p1 = gradient[0], gradient[-1]
                radius = ((p0['x'] - p1['x']) ** 2 + (p0['y'] - p1['y']) ** 2) ** .5
                gradient = f'cx="{p0["x"]}" cy="{p0["y"]}" r="{radius}"'
                stops = graphic['gradientStops']
                yield f'<radialGradient id="gradient{cls.graphic_counter}" {gradient}>'
                for stop in stops:
                    color = stop['color']
                    stop_opacity = opacity * color.get('a', 1)
                    color = color['r'], color['g'], color['b']
                    color = '#{:02x}{:02x}{:02x}'.format(*map(lambda x: int(x * 255), color))
                    yield f'\t<stop offset="{stop["position"]}" stop-color="{color}" stop-opacity="{stop_opacity}"/>'
                yield f'</radialGradient>'
                yield f'<path fill="url(#gradient{cls.graphic_counter})" stroke-width="{stroke_width}" fill-opacity="{opacity}" stroke-opacity="{opacity}" d="{path_data}"/>'
            case _:
                logging.warning(f'Unknown graphic type : {graphic["type"]}')
                return []


class VectorGenerator(DesignGenerator):
    """
    Class used to generate every vector in the design. (Images, Shapes, ...)
    """
    svg_counter: int = 0

    def generate_design(self):
        """
        Generates a QLabel containing a QSvgWidget.
        returns:
            An iterator of strings containing the code to generate a QLabel containing a QSvgWidget.
        """
        VectorGenerator.svg_counter += 1

        svg_filename = f'file{VectorGenerator.svg_counter}.svg'
        pyqt_svg_path = f'svg/' + svg_filename

        SvgGenerator.create_svg_file(self.figma_node, svg_filename)
        svg_widget_name = 'q_svg_widget_' + self.q_widget_name
        width, height = self.figma_node['absoluteBoundingBox']['width'], self.figma_node['absoluteBoundingBox'][
            'height']
        yield from f"""
self.{self.q_widget_name} = QLabel(self.{self.parent.q_widget_name})
self.{self.q_widget_name}.setGeometry({self.pyqt_bounds})
self.{svg_widget_name} = QSvgWidget(self.{self.q_widget_name})
self.{svg_widget_name}.setGeometry(QRect(0, 0, {int(width * config.scale)}, {int(height * config.scale)}))
self.{svg_widget_name}.load("{pyqt_svg_path}")""".splitlines()
