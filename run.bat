@echo off
echo Running Escritura Rapida Game...

REM Run the compiled game
java --module-path "C:\Program Files\Java\javafx-17.0.2\lib" --add-modules javafx.controls,javafx.fxml -cp out com.escriturarapida.EscrituraRapidaApp

pause
