class Alumno: 
    def __init__(self, nombre, presente, grupo, materia):
        self.nombre = nombre
        self.presente = presente
        self.grupo = grupo
        self.materia = materia

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.nombre} - {self.grupo} - {self.materia} - {estado}"