<?php
// Incluir archivos necesarios
// include "encabezado.php";
// include "config.php";
// include "codigos.php";

// Lista de velocidades
$velocidad = array(
    "128k", "256k", "512k", "768k", "1M", "2M", "3M", "4M", "5M", "6M", "7M", "8M", "9M", "10M",
    "20M", "30M", "40M", "50M", "60M", "70M", "80M", "90M", "100M"
);

// Verificar si se envió el formulario
if (isset($_POST['enviar'])) {
    $lineas = $_POST['lineas'] ?? 0;
    $tipo = $_POST['tipo'] ?? '';

    // Verificar si las líneas son 2 o más
    if ($lineas >= 2) {
        ?>
        <form method="post" action="aplicar.php" class="formulario">
            <input type="hidden" name="lineas" value="<?php echo htmlspecialchars($lineas); ?>">
            <input type="hidden" name="tipo" value="<?php echo htmlspecialchars($tipo); ?>">

            <table class="tabla-formulario">
                <tr>
                    <td class="imagen-columna"><img src="red.jpg" alt="Imagen red" class="imagen"></td>
                    <td class="formulario-columna">
                        <table>
                            <tr>
                                <td>WAN del router:</td>
                                <td><input type="text" name="wan" value="WAN" class="input-campo"></td>
                            </tr>
                            <tr>
                                <td>Segmentos de red autorizadas:</td>
                                <td><textarea rows="6" name="lan" class="input-campo">192.168.10.0/24</textarea></td>
                            </tr>
                            <tr>
                                <td>Puertos libres TCP:</td>
                                <td><input type="text" name="puertos_tcp" value="8291,80,8728" class="input-campo"></td>
                            </tr>
                            <tr>
                                <td>Puertos libres UDP:</td>
                                <td><input type="text" name="puertos_udp" value="8291,80,8728" class="input-campo"></td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <input type="submit" name="aceptar" value="Generar tickets" class="btn-submit">
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td class="imagen-columna"><img src="clientes.jpg" alt="Imagen clientes" class="imagen"></td>
                </tr>
                <tr>
                    <td colspan="3" class="mensaje-info">Algo de información adicional aquí.</td>
                </tr>
            </table>
        </form>
        <?php
    } else {
        echo "No puede realizar el balanceo";
    }
}
?>

<?php include "pie_pag.php"; ?>

<!-- Estilos CSS -->
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
    }

    .formulario {
        width: 80%;
        margin: 20px auto;
        padding: 20px;
        background-color: #fff;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .tabla-formulario {
        width: 100%;
        border-collapse: collapse;
    }

    .tabla-formulario td {
        padding: 10px;
        vertical-align: top;
    }

    .imagen-columna {
        text-align: center;
    }

    .imagen {
        width: 100%;
        max-width: 300px;
    }

    .formulario-columna {
        width: 70%;
    }

    .input-campo {
        width: 100%;
        padding: 8px;
        margin: 5px 0;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 14px;
    }

    .btn-submit {
        width: 100%;
        padding: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .btn-submit:hover {
        background-color: #45a049;
    }

    .mensaje-info {
        text-align: center;
        font-size: 16px;
        color: #333;
        padding: 10px;
    }
</style>