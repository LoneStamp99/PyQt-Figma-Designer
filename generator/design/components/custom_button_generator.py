from generator.design.design_generator import DesignGenerator
from generator.design.core.group_generator import GroupGenerator
from generator.properties.visibility_generator import VisibilityGenerator
from generator.design.core.frame_generator import FrameGenerator
from generator.utils import indent


class CustomButtonGenerator(DesignGenerator):
    handler_click_function_name: str
    controller_enable_function_name: str
    controller_disable_function_name: str

    def __init__(self, figma_node, parent, group_generator: GroupGenerator):
        super().__init__(figma_node, parent)
        if len(group_generator.children) < 4:
            raise Exception(f'Custom button {self.q_widget_name} should have at least 4 children')
        self.hide_show_mouse_over_generator = VisibilityGenerator(group_generator.children[-1])
        self.hide_show_pressed_generator = VisibilityGenerator(group_generator.children[-2])
        self.hide_show_disabled_generator = VisibilityGenerator(group_generator.children[-3])

    def generate_design(self):
        self.handler_click_function_name = f'{self.q_widget_name}_clicked'
        self.controller_enable_function_name = f'{self.q_widget_name}_enable'
        self.controller_disable_function_name = f'{self.q_widget_name}_disable'
        enabled_name = f'{self.q_widget_name}_enabled'

        yield from f"""
self.{self.q_widget_name} = QPushButton(self.{self.parent.q_widget_name})
self.{self.q_widget_name}.setGeometry({self.pyqt_bounds})
self.{self.q_widget_name}.setFlat(True)
self.{self.q_widget_name}.setAutoFillBackground(False)
self.{self.q_widget_name}.setObjectName("{self.q_widget_name}")
self.{self.q_widget_name}.setMouseTracking(True)
self.{self.q_widget_name}.setContextMenuPolicy(Qt.NoContextMenu)
self.{self.q_widget_name}.setAcceptDrops(False)
self.{self.q_widget_name}.setFocusPolicy(Qt.NoFocus)
self.{enabled_name} = True""".splitlines()

        # Mouse over
        yield from f"""def __{self.q_widget_name}_mouse_over(*args, **kwargs):
    if self.{enabled_name} :""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('True'), n=2)
        yield from indent(self.hide_show_pressed_generator.generate_set('False'), n=2)
        yield from indent(self.hide_show_disabled_generator.generate_set('False'), n=2)

        # Mouse leave
        yield from f"""def __{self.q_widget_name}_mouse_leave(*args, **kwargs):
    if self.{enabled_name} :""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('False'), n=2)
        yield from indent(self.hide_show_pressed_generator.generate_set('False'), n=2)
        yield from indent(self.hide_show_disabled_generator.generate_set('False'), n=2)

        # Mouse press
        yield from f"""def __{self.q_widget_name}_mouse_press(*args, **kwargs):
    if self.{enabled_name} :""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('False'), n=2)
        yield from indent(self.hide_show_pressed_generator.generate_set('True'), n=2)
        yield from indent(self.hide_show_disabled_generator.generate_set('False'), n=2)

        # Mouse release
        yield from f"""def __{self.q_widget_name}_mouse_release(*args, **kwargs):
    if self.{enabled_name} :""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('True'), n=2)
        yield from indent(self.hide_show_pressed_generator.generate_set('False'), n=2)
        yield from indent(self.hide_show_disabled_generator.generate_set('False'), n=2)
        yield from indent(f'self.{self.q_widget_name}.clicked.emit()', n=2)

        # Disable

        yield from f"""def __{self.q_widget_name}_disable(*args, **kwargs):
    self.{enabled_name} = False""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('False'))
        yield from indent(self.hide_show_pressed_generator.generate_set('False'))
        yield from indent(self.hide_show_disabled_generator.generate_set('True'))
        # disable capture mouse events
        yield from indent(f'self.{self.q_widget_name}.setMouseTracking(False)')
        yield from indent(f'self.{self.q_widget_name}.setFocusPolicy(Qt.NoFocus)')
        yield from indent(f'self.{self.q_widget_name}.setStyleSheet("background-color: rgba(255, 255, 255, 0);")')

        # Enable
        yield from f"""def __{self.q_widget_name}_enable(*args, **kwargs):
    self.{enabled_name} = True""".splitlines()
        yield from indent(self.hide_show_mouse_over_generator.generate_set('False'))
        yield from indent(self.hide_show_pressed_generator.generate_set('False'))
        yield from indent(self.hide_show_disabled_generator.generate_set('False'))
        # enable capture mouse events
        yield from indent(f'self.{self.q_widget_name}.setMouseTracking(True)')

        # Click handler
        yield from f"""
def __{self.handler_click_function_name}(*args, **kwargs):
    try :
        GuiHandler.{self.handler_class_path}.{self.handler_click_function_name}()
    except NameError:
        print("No function {self.handler_click_function_name} defined")
    except Exception as e:
        print("Caught exception while trying to call {self.handler_click_function_name} : " + str(e))
""".splitlines()

        # Connect signals
        yield from f"""
self.{self.q_widget_name}.clicked.connect(__{self.handler_click_function_name})
self.{self.q_widget_name}.enterEvent = __{self.q_widget_name}_mouse_over
self.{self.q_widget_name}.leaveEvent = __{self.q_widget_name}_mouse_leave
self.{self.q_widget_name}.mousePressEvent = __{self.q_widget_name}_mouse_press
self.{self.q_widget_name}.mouseReleaseEvent = __{self.q_widget_name}_mouse_release
self.{self.q_widget_name}.disable = __{self.q_widget_name}_disable
self.{self.q_widget_name}.enable = __{self.q_widget_name}_enable""".splitlines()

        # Connect controller
        yield from f"""
try :
    GuiController.{self.controller_class_path}.{self.controller_enable_function_name} = self.{self.q_widget_name}.enable
except NameError:
    print("No function {self.controller_enable_function_name} defined")
except Exception as e:
    print("Error while linking {self.controller_enable_function_name} to {self.controller_class_path}.{self.controller_enable_function_name} : " + str(e))
    
try :
    GuiController.{self.controller_class_path}.{self.controller_disable_function_name} = self.{self.q_widget_name}.disable
except NameError :
    print("No function {self.controller_disable_function_name} defined")
except Exception as e:
    print("Error while linking {self.controller_disable_function_name} to {self.controller_class_path}.{self.controller_disable_function_name} : " + str(e))
""".splitlines()

        # hide the mouse over, pressed and disabled children
        yield from self.hide_show_mouse_over_generator.generate_set('False')
        yield from self.hide_show_pressed_generator.generate_set('False')
        yield from self.hide_show_disabled_generator.generate_set('False')

    def generate_handler(self):
        yield from f"""
@classmethod
def {self.handler_click_function_name}(cls):
    print("CustomButton {self.q_widget_name} clicked")
""".splitlines()

    def generate_controller(self):
        yield from f"""
@classmethod
def {self.controller_enable_function_name}(cls):
     print("The function {self.controller_enable_function_name} is unfortunately not linked to the controller")
 
@classmethod
def {self.controller_disable_function_name}(cls):
        print("The function {self.controller_disable_function_name} is unfortunately not linked to the controller")
""".splitlines()
