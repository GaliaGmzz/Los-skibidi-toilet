import flet as ft

class AsistenciaView:

    def __init__(self, page: ft.Page):
        self.page = page

        self.page.title = "Sistema de Asistencia"
        self.page.window_width = 500
        self.page.window_height = 600
        self.page.padding = 20

        self.txt_nombre = ft.TextField(
            label = "Nombre del Alumno",
            width = 400
        )

        self.chk_presente = ft.Checkbox(
            label = "Presente"
        )

        self.btn_registrar = ft.ElevatedButton(
            "Registrar Asistencia",
            width = 250
        )

        self.lbl_mensaje = ft.Text(
            value = "",
            size = 16
        )

        self.lista_registros = ft.Column()

    def contruirInterfaz(self):

        return ft.Column(
            controls = [
                ft.Text(
                    "Registro de Asistencia",
                    size = 30,
                    weight = "bold"
                ),

                ft.Divider(),

                self.txt_nombre,
                self.chk_presente,
                self.btn_registrar,
                self.lbl_mensaje,

                ft.Text(
                    "Lista de registros",
                    size = 20,
                    weight = "bold"
                ),
                self.lista_registros

            ]
        )
    
    def agregar_texto(self, texto):
        return ft.Text(value = texto, size = 16)

