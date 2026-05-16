class Alumno: 
    def __init__(self, nombre, presente):
        self.nombre = nombre
        self.presente = presente

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.nombre} - {estado}"