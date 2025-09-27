@echo off
echo Building Escritura Rapida Game...

REM Create output directory
if not exist "out" mkdir out

REM Compile the Java files
echo Compiling Java files...
javac --module-path "C:\Program Files\Java\javafx-17.0.2\lib" --add-modules javafx.controls,javafx.fxml -d out src\main\java\module-info.java src\main\java\com\escriturarapida\*.java src\main\java\com\escriturarapida\controllers\*.java src\main\java\com\escriturarapida\models\*.java

if %ERRORLEVEL% EQU 0 (
    echo Compilation successful!
    echo.
    echo To run the game, use:
    echo java --module-path "C:\Program Files\Java\javafx-17.0.2\lib" --add-modules javafx.controls,javafx.fxml -cp out com.escriturarapida.EscrituraRapidaApp
) else (
    echo Compilation failed!
)

pause
