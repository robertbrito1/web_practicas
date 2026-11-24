"""
Motor de preguntas frecuentes del asistente (no usa IA ni red: coste 0).

Es la ÚNICA fuente de información del chat: el asistente con IA (chat/ia.py)
construye su prompt a partir de estas mismas entradas, así que basta con editar
este archivo para cambiar lo que sabe el bot.

NOTA: es una web de portafolio. Las sedes, el contacto, los ciclos, las becas y
las certificaciones salen de las páginas del propio sitio; los demás datos
(turnos, proceso de inscripción, modalidad) son de ejemplo.

Cómo decide la respuesta:
  1. Normaliza el texto (minúsculas, sin tildes ni signos).
  2. Cada entrada tiene "claves" con un peso; se suman las que aparecen.
  3. Gana la entrada con más puntos si llega al umbral; si no, no hay respuesta.
  Una clave que acaba en "*" admite cualquier terminación ("curso*" -> cursos).
  Sin "*" debe coincidir la palabra completa ("dam" no coincide con "dame").
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union

UMBRAL = 2

TELEFONO = "900 852 425"
EMAIL = "info@grupoeuroformac.com"
WEB_CURSOS_SUBVENCIONADOS = "https://cursosgratuitos.grupoeuroformac.com/"


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin signos y con espacios simples."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


@dataclass(frozen=True)
class Entrada:
    id: str
    pregunta: str                      # forma canónica (botones y prompt de la IA)
    claves: Tuple[Tuple[str, int], ...]
    respuesta: Union[str, Callable[[], str]]
    sugerencias: Tuple[str, ...] = ()
    max_palabras: Optional[int] = None  # para saludos: solo si el mensaje es corto

    def texto(self) -> str:
        return self.respuesta() if callable(self.respuesta) else self.respuesta


@dataclass(frozen=True)
class Respuesta:
    texto: str
    sugerencias: Tuple[str, ...]
    entrada_id: str


# Preguntas que se ofrecen como botones. Cada una debe resolver a su entrada
# (lo comprueba un test).
SUGERENCIAS_INICIALES = (
    "¿Qué cursos ofrecéis?",
    "¿Cómo funciona la Beca MEC?",
    "¿Dónde están las sedes?",
    "¿Cómo me inscribo?",
    "¿Cuánto cuesta estudiar?",
    "Quiero hablar con una persona",
)

SUGERENCIAS_GENERALES = SUGERENCIAS_INICIALES[:4]


def _profesores() -> str:
    """Respuesta dinámica: lee el equipo docente de la base de datos."""
    from inicio.models import Profesor  # import tardío: evita problemas al arrancar Django

    lineas = [
        f"• {p.nombre} {p.apellido}: {p.asignaturas} ({p.experiencia} años de experiencia)"
        for p in Profesor.objects.all().order_by("nombre")
    ]
    if not lineas:
        return "Puedes conocer a nuestro equipo docente en /equipo."
    return "Nuestro equipo docente:\n" + "\n".join(lineas) + "\n\nPuedes ver sus fichas completas en /equipo."


ENTRADAS: Tuple[Entrada, ...] = (
    Entrada(
        id="saludo",
        pregunta="Hola",
        claves=(("hola*", 3), ("buenas", 3), ("buenos dias", 3), ("buenas tardes", 3),
                ("buenas noches", 3), ("hey", 3), ("saludos", 3), ("que tal", 3)),
        max_palabras=4,
        respuesta=("¡Hola! 👋 Soy el asistente virtual de FP Euroformac. Puedo ayudarte con "
                   "cursos, becas, sedes, inscripción y contacto. ¿Qué te gustaría saber?"),
        sugerencias=SUGERENCIAS_INICIALES[:4],
    ),
    Entrada(
        id="gracias",
        pregunta="Gracias",
        claves=(("gracias", 3), ("muchas gracias", 3), ("adios", 3), ("hasta luego", 3),
                ("chao", 3), ("agur", 3), ("perfecto", 2), ("genial", 2)),
        max_palabras=5,
        respuesta="¡De nada! Si necesitas algo más, aquí estaré. ¡Que tengas un buen día! 😊",
    ),
    Entrada(
        id="precio",
        pregunta="¿Cuánto cuesta estudiar?",
        claves=(("precio*", 3), ("cuesta*", 3), ("coste*", 3), ("costo*", 3), ("pagar", 2),
                ("gratis", 3), ("gratuit*", 3), ("subvencion*", 3), ("mensualidad*", 3),
                ("tarifa*", 2), ("dinero", 1)),
        respuesta=("El coste depende del ciclo y de la modalidad. Muchos de nuestros cursos son "
                   f"100% subvencionados (puedes verlos en {WEB_CURSOS_SUBVENCIONADOS}) y en la "
                   "formación reglada puedes solicitar la Beca MEC.\n\n"
                   f"Para un presupuesto personalizado, contacta con admisiones: {TELEFONO} o {EMAIL}."),
        sugerencias=("¿Cómo funciona la Beca MEC?", "¿Cómo me inscribo?"),
    ),
    Entrada(
        id="beca",
        pregunta="¿Cómo funciona la Beca MEC?",
        claves=(("beca*", 3), ("mec", 3), ("ministerio", 2), ("ayuda*", 1), ("solicitud*", 1)),
        respuesta=("La Beca MEC se solicita normalmente entre abril y julio en la web del Ministerio "
                   "de Educación. Puede cubrir transporte, material, matrícula y, según el caso, parte "
                   "del alojamiento.\n\nTe orientamos con el proceso desde admisiones."),
        sugerencias=("¿Cómo me inscribo?", "¿Cuánto cuesta estudiar?"),
    ),
    Entrada(
        id="requisitos",
        pregunta="¿Qué requisitos de acceso hay?",
        claves=(("requisito*", 3), ("acceso", 2), ("bachillerato", 3), ("titulo*", 2),
                ("prueba*", 2), ("edad", 2), ("necesito", 1), ("mayor*", 1)),
        respuesta=("Para un ciclo de Grado Superior (DAM, DAW, ASIR) lo habitual es tener Bachillerato, "
                   "un Grado Medio o superar la prueba de acceso (mayores de 19 años). En ASIR no "
                   "necesitas conocimientos previos, aunque se recomienda interés por la informática.\n\n"
                   "Confirma tu caso concreto con admisiones."),
        sugerencias=("¿Cómo me inscribo?", "¿Qué cursos ofrecéis?"),
    ),
    Entrada(
        id="duracion",
        pregunta="¿Cuánto dura y qué horarios hay?",
        claves=(("duracion", 3), ("dura*", 3), ("cuanto tiempo", 3), ("horario*", 3), ("turno*", 3),
                ("horas", 2), ("anos", 1)),
        respuesta=("Los ciclos de Grado Superior duran 2 cursos académicos (unas 2.000 horas, incluidas "
                   "las prácticas en empresa). Ofrecemos turnos de mañana y de tarde según la sede y la "
                   "disponibilidad de plazas."),
        sugerencias=("¿Dónde están las sedes?", "¿Cómo me inscribo?"),
    ),
    Entrada(
        id="inscripcion",
        pregunta="¿Cómo me inscribo?",
        claves=(("inscri*", 3), ("matricul*", 3), ("apunt*", 3), ("plazo*", 2), ("admision*", 2),
                ("plaza*", 2), ("comienzo", 2), ("empezar", 1)),
        respuesta=("Inscribirte es sencillo:\n"
                   "1) Elige tu ciclo o curso.\n"
                   "2) Escríbenos desde el formulario de /contacto/ o llama al " + TELEFONO + ".\n"
                   "3) Te indicamos la documentación y los plazos de la convocatoria.\n\n"
                   "Te acompañamos en todo el proceso."),
        sugerencias=("¿Qué requisitos de acceso hay?", "¿Cómo funciona la Beca MEC?"),
    ),
    Entrada(
        id="modalidad",
        pregunta="¿La formación es presencial u online?",
        claves=(("online", 3), ("presencial*", 3), ("distancia", 3), ("semipresencial*", 3),
                ("plataforma", 2), ("remoto", 2)),
        respuesta=("La formación es presencial en nuestros centros, y además contamos con una plataforma "
                   "online para contenidos y seguimiento. Pregunta a admisiones por la modalidad de cada ciclo."),
        sugerencias=("¿Dónde están las sedes?", "¿Qué cursos ofrecéis?"),
    ),
    Entrada(
        id="dam",
        pregunta="¿Qué se aprende en DAM?",
        claves=(("dam", 3), ("multiplataforma", 3), ("java", 2), ("moviles", 1)),
        respuesta=("DAM (Desarrollo de Aplicaciones Multiplataforma) se enfoca en aplicaciones móviles y "
                   "de escritorio, bases de datos y Java.\n\nSalidas: desarrollador de apps, programador "
                   "Java o soporte multiplataforma."),
        sugerencias=("¿Qué se estudia en DAW?", "¿Qué incluye ASIR?", "¿Qué salidas laborales hay?"),
    ),
    Entrada(
        id="daw",
        pregunta="¿Qué se estudia en DAW?",
        claves=(("daw", 3), ("aplicaciones web", 3), ("frontend", 2), ("backend", 2), ("php", 2),
                ("html", 2), ("css", 1), ("javascript", 2), ("mysql", 2)),
        respuesta=("DAW (Desarrollo de Aplicaciones Web) cubre desarrollo web: frontend (HTML, CSS, "
                   "JavaScript) y backend (PHP, MySQL).\n\nMuchos titulados trabajan por cuenta propia "
                   "como freelance creando webs."),
        sugerencias=("¿Qué se aprende en DAM?", "¿Qué incluye ASIR?", "¿Qué salidas laborales hay?"),
    ),
    Entrada(
        id="asir",
        pregunta="¿Qué incluye ASIR?",
        claves=(("asir", 3), ("ciberseguridad", 3), ("servidores", 2), ("administracion de sistemas", 3),
                ("redes", 1), ("sistemas", 1)),
        respuesta=("ASIR (Administración de Sistemas Informáticos en Red) incluye administración de "
                   "redes, servidores, ciberseguridad y sistemas.\n\nNo requiere conocimientos previos, "
                   "aunque se recomienda interés por la informática y las redes."),
        sugerencias=("¿Qué se aprende en DAM?", "¿Qué se estudia en DAW?", "¿Qué requisitos de acceso hay?"),
    ),
    Entrada(
        id="cursos",
        pregunta="¿Qué cursos ofrecéis?",
        claves=(("curso*", 2), ("ciclo*", 2), ("formacion", 2), ("estudiar", 2), ("oferta*", 3),
                ("ofreceis", 3), ("titulacion*", 3), ("grado*", 2), ("fp", 2), ("carrera*", 1)),
        respuesta=("Ofrecemos formación reglada en tecnología:\n"
                   "• DAM: Desarrollo de Aplicaciones Multiplataforma\n"
                   "• DAW: Desarrollo de Aplicaciones Web\n"
                   "• ASIR: Administración de Sistemas Informáticos en Red\n\n"
                   f"Además hay cursos subvencionados: {WEB_CURSOS_SUBVENCIONADOS}\n"
                   "Pregúntame por cada ciclo si quieres más detalle."),
        sugerencias=("¿Qué se aprende en DAM?", "¿Qué se estudia en DAW?", "¿Qué incluye ASIR?"),
    ),
    Entrada(
        id="salidas",
        pregunta="¿Qué salidas laborales hay?",
        claves=(("salida*", 3), ("trabajo*", 2), ("empleo", 3), ("laboral*", 2), ("freelance*", 3),
                ("autonomo*", 2), ("practicas", 2), ("fct", 3), ("bolsa", 2)),
        respuesta=("Las salidas dependen del ciclo:\n"
                   "• DAM: desarrollador de apps, programador Java, soporte multiplataforma.\n"
                   "• DAW: desarrollo web; muchos titulados trabajan como freelance.\n"
                   "• ASIR: administración de redes, servidores y ciberseguridad.\n\n"
                   "Durante el ciclo realizas prácticas en empresas."),
        sugerencias=("¿Qué cursos ofrecéis?", "¿Cómo me inscribo?"),
    ),
    Entrada(
        id="sedes",
        pregunta="¿Dónde están las sedes?",
        claves=(("sede*", 3), ("donde", 2), ("direccion*", 3), ("ubicacion*", 3), ("ubicad*", 3),
                ("madrid", 2), ("valencia", 2), ("murcia", 2), ("malaga", 2), ("lorca", 2),
                ("yecla", 2), ("mapa", 2), ("como llegar", 3), ("centro*", 1)),
        respuesta=("Estamos en cuatro ciudades:\n"
                   "• Madrid: Cl. de Ayala, 87 (Salamanca) y Av. de Pablo Iglesias, 53 (Ciudad Universitaria).\n"
                   "• Valencia: Av. Burjasot, 93 y Calle Duque de Mandas, 41.\n"
                   "• Murcia: Paseo de Florencia, 22 y 46; también en Lorca (C. Ricardo Carrillo, 6) y Yecla (C. Lorca, 1).\n"
                   "• Málaga: Avenida de Andalucía, 31.\n\n"
                   "Verás los mapas en /contacto/."),
        sugerencias=("¿Cómo me inscribo?", "¿La formación es presencial u online?"),
    ),
    Entrada(
        id="contacto",
        pregunta="¿Cómo puedo contactar con vosotros?",
        claves=(("contact*", 3), ("telefono*", 3), ("correo*", 3), ("email", 3), ("mail", 3),
                ("llamar*", 2), ("escribir*", 2), ("persona", 3), ("humano", 3), ("asesor*", 3),
                ("operador*", 3), ("agente", 2), ("alguien", 2), ("redes sociales", 3), ("hablar", 1)),
        respuesta=(f"Puedes contactar con nosotros:\n"
                   f"• Teléfono: {TELEFONO}\n"
                   f"• Email: {EMAIL}\n"
                   "• Formulario: /contacto/\n\n"
                   "También estamos en X (Twitter), Facebook, LinkedIn e Instagram (@grupoeuroformac)."),
        sugerencias=("¿Cómo me inscribo?", "¿Dónde están las sedes?"),
    ),
    Entrada(
        id="profesores",
        pregunta="¿Quiénes son los profesores?",
        claves=(("profesor*", 3), ("docente*", 3), ("equipo", 2), ("quien da clase", 3), ("claustro", 3)),
        respuesta=_profesores,
        sugerencias=("¿Qué cursos ofrecéis?", "¿Cómo puedo contactar con vosotros?"),
    ),
    Entrada(
        id="certificaciones",
        pregunta="¿Qué certificaciones de calidad tenéis?",
        claves=(("certificac*", 3), ("calidad", 2), ("iso", 3), ("acreditac*", 3), ("homologad*", 2),
                ("trinity", 3), ("toeic", 3)),
        respuesta=("Contamos con certificaciones y acreditaciones de calidad como ISO 14001, OHSAS 18001, "
                   "Madrid Excelente, y somos centro examinador de Trinity College London y TOEIC. "
                   "Puedes verlas en la sección «Certificaciones» de la página de inicio."),
    ),
    Entrada(
        id="rsc",
        pregunta="¿Qué hacéis en responsabilidad social?",
        claves=(("rsc", 3), ("solidari*", 3), ("patrocin*", 3), ("banco de alimentos", 3),
                ("responsabilidad", 2), ("deporte", 1), ("chamberi", 2)),
        respuesta=("Estamos comprometidos con nuestro entorno: colaboramos con el Banco de Alimentos de "
                   "Madrid con recogidas de alimentos en nuestro Centro Tecnológico de Ciudad Universitaria, "
                   "y patrocinamos al club deportivo vecino porque creemos en el deporte como parte de la "
                   "vida de nuestros alumnos.\n\nMás información en /rsc."),
    ),
    Entrada(
        id="nosotros",
        pregunta="¿Quiénes sois?",
        claves=(("quienes somos", 3), ("quienes sois", 3), ("quien sois", 3), ("que sois", 3),
                ("a que os dedicais", 3), ("sobre nosotros", 3), ("sobre vosotros", 3), ("historia", 2),
                ("experiencia", 2), ("que es euroformac", 3), ("euroformac", 1)),
        respuesta=("FP Euroformac lleva más de 25 años formando personas. Nuestro objetivo es diagnosticar, "
                   "planificar, ejecutar y evaluar las necesidades de formación de empresas, organizaciones "
                   "y particulares, con metodologías y herramientas innovadoras.\n\nMás en /nosotros."),
        sugerencias=("¿Qué cursos ofrecéis?", "¿Qué certificaciones de calidad tenéis?"),
    ),
    Entrada(
        id="legal",
        pregunta="¿Dónde veo la política de privacidad y cookies?",
        claves=(("privacidad", 3), ("cookie*", 3), ("datos personales", 3), ("proteccion de datos", 3),
                ("aviso legal", 3), ("rgpd", 3), ("legal", 2)),
        respuesta=("Puedes consultar nuestra información legal aquí:\n"
                   "• Política de privacidad: /politicas\n"
                   "• Política de cookies: /cockies\n"
                   "• Aviso legal: /avisos"),
    ),
    Entrada(
        id="bot",
        pregunta="¿Quién eres?",
        claves=(("quien eres", 3), ("que eres", 3), ("eres un bot", 3), ("eres una ia", 3),
                ("chatbot", 3), ("inteligencia artificial", 2), ("eres real", 3), ("eres humano", 3)),
        respuesta=("Soy el asistente virtual de FP Euroformac: un programa que responde preguntas "
                   f"frecuentes con la información de esta web. Si necesitas hablar con una persona, "
                   f"llama al {TELEFONO}."),
    ),
)

MENSAJE_SIN_RESPUESTA = (
    "No tengo información sobre eso 😅. Puedo ayudarte con cursos, becas, sedes, inscripción o contacto.\n\n"
    f"Para otras dudas, escribe a {EMAIL} o llama al {TELEFONO}."
)


def _compilar(clave: str) -> "re.Pattern[str]":
    prefijo = clave.endswith("*")
    base = re.escape(normalizar(clave.rstrip("*")))
    return re.compile(r"(?<![a-z0-9])" + base + (r"[a-z0-9]*" if prefijo else r"(?![a-z0-9])"))


# Se compila una sola vez al importar el módulo.
_PATRONES = {
    entrada.id: tuple((_compilar(clave), peso) for clave, peso in entrada.claves)
    for entrada in ENTRADAS
}
_POR_ID = {entrada.id: entrada for entrada in ENTRADAS}


def puntuar(entrada: Entrada, texto_normalizado: str) -> int:
    return sum(peso for patron, peso in _PATRONES[entrada.id] if patron.search(texto_normalizado))


def responder(mensaje: str) -> Optional[Respuesta]:
    """Devuelve la mejor respuesta del FAQ o None si no hay coincidencia suficiente."""
    texto = normalizar(mensaje)
    if not texto:
        return None
    palabras = len(texto.split())

    # Las cortesías (saludos, gracias) solo responden si no hay ninguna pregunta de contenido:
    # "hola, ¿qué cursos tenéis?" debe contestar a los cursos, no al saludo.
    for cortesias in (False, True):
        mejor, mejor_puntos = None, 0
        for entrada in ENTRADAS:  # el orden desempata: lo más específico va primero
            es_cortesia = entrada.max_palabras is not None
            if es_cortesia != cortesias:
                continue
            if es_cortesia and palabras > entrada.max_palabras:
                continue
            puntos = puntuar(entrada, texto)
            if puntos > mejor_puntos:
                mejor, mejor_puntos = entrada, puntos
        if mejor is not None and mejor_puntos >= UMBRAL:
            return _respuesta(mejor)
    return None


def _respuesta(mejor: Entrada) -> Respuesta:
    return Respuesta(
        texto=mejor.texto(),
        sugerencias=mejor.sugerencias or SUGERENCIAS_GENERALES,
        entrada_id=mejor.id,
    )


def base_de_conocimiento() -> str:
    """Texto con toda la información oficial (lo usa el prompt de la IA)."""
    bloques = []
    for entrada in ENTRADAS:
        if entrada.max_palabras is not None:  # saludos y despedidas no aportan información
            continue
        bloques.append(f"P: {entrada.pregunta}\nR: {entrada.texto()}")
    return "\n\n".join(bloques)
