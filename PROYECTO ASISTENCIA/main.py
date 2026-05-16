import flet as ft
from vista.asistenciaView import AsistenciaView
from controller.asistenciaController import AsistenciaController

def main(page: ft.Page):
    
    vista = AsistenciaView(page)

    controller = AsistenciaController(vista)
    vista.btn_registrar.on_click = controller.registrarAsistencia

    page.add(
        vista.contruirInterfaz()
    )

ft.app(target = main)