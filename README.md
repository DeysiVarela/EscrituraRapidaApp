# Escritura R�pida - Fast Writing Game

## Descripci�n
Juego de habilidad desarrollado en Java con JavaFX donde los jugadores deben escribir palabras que aparecen en pantalla antes de que se acabe el tiempo. El juego se desarrolla por niveles con dificultad progresiva.

## Caracter�sticas
- **Interfaz gr�fica moderna** con JavaFX
- **Sistema de niveles** con dificultad progresiva
- **Temporizador** que se reduce cada 5 niveles
- **Validaci�n exacta** de palabras
- **Retroalimentaci�n visual** inmediata
- **Sistema de puntuaci�n**

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
               GameModel.java (L�gica del juego)
    resources/
        com/escriturarapida/
            game-view.fxml (Interfaz gr�fica)
```

## Funcionalidades Implementadas

### HU-1: Visualizaci�n de palabra aleatoria y validaci�n
-  Muestra palabras aleatorias al iniciar cada nivel
-  Campo de texto para escribir la respuesta
-  Validaci�n al presionar Enter o bot�n Enviar
-  Comparaci�n exacta (letras, espacios, may�sculas, puntuaci�n)
-  Mensajes de error claros

### HU-2: Control del tiempo por nivel
-  Tiempo inicial de 20 segundos por nivel
-  Temporizador visible que se actualiza en tiempo real
-  Validaci�n autom�tica al finalizar el tiempo
-  Informaci�n clara cuando se agota el tiempo

### HU-3: Progresi�n del juego y aumento de dificultad
-  Incremento autom�tico de nivel al acertar
-  Cada nivel representa una respuesta correcta consecutiva
-  Reducci�n de tiempo cada 5 niveles (m�nimo 2 segundos)
-  El jugador permanece en el mismo nivel si falla

### HU-4: Retroalimentaci�n visual y mensajes
-  Mensajes positivos al acertar ("�Correcto!", "�Nivel superado!")
-  Mensajes de error claros ("Incorrecto", "Tiempo agotado")
-  Resumen final con estad�sticas
-  Opci�n de reiniciar el juego

## C�mo Ejecutar

### Opci�n 1: IntelliJ IDEA
1. Abrir el proyecto en IntelliJ IDEA
2. Configurar JavaFX SDK en Project Structure
3. Ejecutar `EscrituraRapidaApp.java`

### Opci�n 2: L�nea de comandos
```bash
# Compilar
javac --module-path /path/to/javafx/lib --add-modules javafx.controls,javafx.fxml -d out src/main/java/module-info.java src/main/java/com/escriturarapida/*.java src/main/java/com/escriturarapida/controllers/*.java src/main/java/com/escriturarapida/models/*.java

# Ejecutar
java --module-path /path/to/javafx/lib --add-modules javafx.controls,javafx.fxml -cp out com.escriturarapida.EscrituraRapidaApp
```

## Tecnolog�as Utilizadas
- **Java SE 17+**: Lenguaje de programaci�n
- **JavaFX**: Librer�a gr�fica para la interfaz
- **FXML**: Definici�n de interfaces gr�ficas
- **Scene Builder**: Herramienta de dise�o (opcional)

## Arquitectura
El proyecto sigue el patr�n MVC (Model-View-Controller):
- **Model**: `GameModel` - Maneja la l�gica del juego
- **View**: `game-view.fxml` - Define la interfaz gr�fica
- **Controller**: `GameController` - Controla las interacciones

## Documentaci�n
Todo el c�digo est� documentado con Javadoc en ingl�s, siguiendo las convenciones del curso.

## Autor
Deysi Yuliana Rivas Varela - Curso de Fundamentos de Programaci�n Orientada a Eventos