# Escritura Rápida - Fast Writing Game

## Descripción
Juego de habilidad desarrollado en Java con JavaFX donde los jugadores deben escribir palabras que aparecen en pantalla antes de que se acabe el tiempo. El juego se desarrolla por niveles con dificultad progresiva.

## Características
- **Interfaz gráfica moderna** con JavaFX
- **Sistema de niveles** con dificultad progresiva
- **Temporizador** que se reduce cada 5 niveles
- **Validación exacta** de palabras
- **Retroalimentación visual** inmediata
- **Sistema de puntuación**

## Requisitos
- Java SE 17 o superior
- JavaFX SDK
- IntelliJ IDEA (recomendado)

## Estructura del Proyecto
```
src/
 main/
    java/
       module-info.java
       com/escriturarapida/
           EscrituraRapidaApp.java (Clase principal)
           controllers/
              GameController.java (Controlador del juego)
           models/
               GameModel.java (Lógica del juego)
    resources/
        com/escriturarapida/
            game-view.fxml (Interfaz gráfica)
```

## Funcionalidades Implementadas

### HU-1: Visualización de palabra aleatoria y validación
-  Muestra palabras aleatorias al iniciar cada nivel
-  Campo de texto para escribir la respuesta
-  Validación al presionar Enter o botón Enviar
-  Comparación exacta (letras, espacios, mayúsculas, puntuación)
-  Mensajes de error claros

### HU-2: Control del tiempo por nivel
-  Tiempo inicial de 20 segundos por nivel
-  Temporizador visible que se actualiza en tiempo real
-  Validación automática al finalizar el tiempo
-  Información clara cuando se agota el tiempo

### HU-3: Progresión del juego y aumento de dificultad
-  Incremento automático de nivel al acertar
-  Cada nivel representa una respuesta correcta consecutiva
-  Reducción de tiempo cada 5 niveles (mínimo 2 segundos)
-  El jugador permanece en el mismo nivel si falla

### HU-4: Retroalimentación visual y mensajes
-  Mensajes positivos al acertar ("¡Correcto!", "¡Nivel superado!")
-  Mensajes de error claros ("Incorrecto", "Tiempo agotado")
-  Resumen final con estadísticas
-  Opción de reiniciar el juego

## Cómo Ejecutar

### Opción 1: IntelliJ IDEA
1. Abrir el proyecto en IntelliJ IDEA
2. Configurar JavaFX SDK en Project Structure
3. Ejecutar `EscrituraRapidaApp.java`

### Opción 2: Línea de comandos
```bash
# Compilar
javac --module-path /path/to/javafx/lib --add-modules javafx.controls,javafx.fxml -d out src/main/java/module-info.java src/main/java/com/escriturarapida/*.java src/main/java/com/escriturarapida/controllers/*.java src/main/java/com/escriturarapida/models/*.java

# Ejecutar
java --module-path /path/to/javafx/lib --add-modules javafx.controls,javafx.fxml -cp out com.escriturarapida.EscrituraRapidaApp
```

## Tecnologías Utilizadas
- **Java SE 17+**: Lenguaje de programación
- **JavaFX**: Librería gráfica para la interfaz
- **FXML**: Definición de interfaces gráficas
- **Scene Builder**: Herramienta de diseño (opcional)

## Arquitectura
El proyecto sigue el patrón MVC (Model-View-Controller):
- **Model**: `GameModel` - Maneja la lógica del juego
- **View**: `game-view.fxml` - Define la interfaz gráfica
- **Controller**: `GameController` - Controla las interacciones

## Documentación
Todo el código está documentado con Javadoc en inglés, siguiendo las convenciones del curso.

## Autor
Estudiante - Curso de Fundamentos de Programación Orientada a Eventos
