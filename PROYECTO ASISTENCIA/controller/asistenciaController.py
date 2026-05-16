from modelo.alumno import Alumno

class AsistenciaController:

    def __init__(self, vista):
        self.vista = vista
        self.lista_alumnos = []

    def registrarAsistencia(self, e):
        try:
            # Obtener los valores
            nombre = self.vista.txt_nombre.value
            presente = self.vista.chk_presente.value

            if nombre == "":
                self.vista.lbl_mensaje.value = "Debe escribir un nombre"
                self.vista.lbl_mensaje.color = "red"
                self.vista.page.update()
                return
            
            if len(nombre) > 10:
                raise Exception("El nombre del alumno no debe exceder 10 caracteres")
            
            # Crear objeto alumno
            alumno = Alumno(nombre, presente)
            self.lista_alumnos.append(alumno)

            # Mostrar listado
            self.vista.lista_registros.controls.append(
                self.vista.agregar_texto(str(alumno))
            )
            
            self.vista.lbl_mensaje.value = "Asistencia registrada exitosamente"
            self.vista.lbl_mensaje.color = "green"
        
            # Limpiar campos
            self.vista.txt_nombre.value = ""
            self.vista.chk_presente.value = False

            self.vista.page.update()

        except Exception as ex:
            self.vista.lbl_mensaje.value = str(ex) if str(ex) else "Error en los datos"
            self.vista.lbl_mensaje.color = "red"
            self.vista.page.update()