
    <?php 
include "encabezado.php";
include "config.php";
session_start();

// Si ya hay una sesión iniciada, mostrar el nombre de la sesión y opción de cerrar
if (isset($_SESSION['codigo'])) {
    echo "<h4 align='right'>Sesión iniciada: " . $_SESSION['codigo'] . " <a href='cerrar.php' name='modificar'>Cerrar</a></h4>";
}

// Si hay un error con el código, mostrar el mensaje y opciones de pago
if (isset($_GET['error']) && $_GET['error'] == "cod") {
    ?>
    <div class="alert">
        <h4>Clave de ingreso incorrecto, debe adquirir una clave de ingreso, <br>durante la vigencia de su clave de ingreso puede generar todos los scripts que desee</h4>
        <div class="payment-options">
            <div class="payment-option">
                <b>Paypal</b><br>
                <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
                    <input type="hidden" name="cmd" value="_s-xclick">
                    <input type="hidden" name="hosted_button_id" value="2WR9DQF2GGAKL">
                    <table>
                        <tr><td><input type="hidden" name="on0" value="Planes">Planes</td></tr>
                        <tr><td>
                            <select name="os0">
                                <option value="1 Mes">3 Meses $19.00 USD</option>
                                <option value="2 Meses">6 Meses $29.00 USD</option>
                                <option value="6 Meses">1 Año $69.00 USD</option>
                                <option value="1 Año">2 Años $99.00 USD</option>
                            </select>
                        </td></tr>
                    </table>
                    <input type="hidden" name="currency_code" value="USD">
                    <input type="image" src="https://www.paypalobjects.com/es_XC/MX/i/btn/btn_buynowCC_LG.gif" border="0" name="submit" alt="PayPal, la forma más segura y rápida de pagar en línea.">
                </form>
            </div>

            <div class="payment-option">
                <b>MercadoPago, <br>Plan 3 Meses 399 pesos</b><br>
                <a mp-mode="dftl" href="https://www.mercadopago.com/mlm/checkout/start?pref_id=86218906-98417d55-82e7-43df-9c1e-6d81c516c381" name="MP-payButton" class="blue-ar-l-rn-none">Pagar</a>
            </div>
        </div>

        <p>• Puede pagar en OXXO al número de cuenta Bancomer: 4152313129329749<br>
        • Para transferencia bancaria utiliza la CLABE Bancomer: 012180014043968980<br>
        • Otros métodos de pago favor de enviar correo a: info@mubu.com.mx <br>
        • Mensaje por whatsapp: 722 55 309 14</p>
    </div>
    <?php
}

// Si la sesión está iniciada, se obtienen las configuraciones
if (isset($_SESSION['tipo'])) {
    $tipo_config = $_SESSION['tipo'];
    $linea = $_SESSION['lineas'] ?? 3;
} else {
    $tipo_config = 'PCC';
    $linea = 3;
}

// Variables para los tipos de configuración
$tipos = [
    'ECMP' => 'Balanceo ECMP',
    'ECMPr' => 'Balanceo ECMP con DNS recursivo',
    'PCC' => 'Balanceo PCC',
    'PCCr' => 'Balanceo PCC con DNS recursivo V6',
    'PCCrV7' => 'Balanceo PCC con DNS recursivo V7',
    'PCC-DYNAMIC' => 'Balanceo PCC Dinámico',
    'PBr' => 'Balanceo PBR con DNS recursivo V6',
    'PBrV7' => 'Balanceo PBR con DNS recursivo V7',
    'NTH' => 'Balanceo NTH',
    'NTHr' => 'Balanceo NTH con DNS recursivo',
    'Hotspot' => 'Hotspot',
    'Tickets' => 'Tickets Hotspot',
    'Firewall' => 'Firewall',
    'Residenciales' => 'Clientes residenciales'
];
?>

<div class="form-container">
    <h3>Cree su Script de configuración para Mikrotik</h3>
    <form method="post" action="parametros.php">
        <div class="form-group">
            <label for="tipo">Tipo de configuración:</label>
            <select id="tipo" name="tipo" onclick="habilita()">
                <?php
                foreach ($tipos as $key => $label) {
                    echo '<option value="' . $key . '" ' . ($_SESSION['tipo'] == $key ? 'selected' : '') . '>' . $label . '</option>';
                }
                ?>
            </select>
        </div>

        <div class="form-group">
            <label for="lineas">Líneas a balancear:</label>
            <select name="lineas" id="lineas">
                <?php
                for ($i = 2; $i <= 12; $i++) {
                    echo '<option value="' . $i . '" ' . ($i == $linea ? 'selected' : '') . '>' . $i . '</option>';
                }
                ?>
            </select>
        </div>

        <div class="form-group">
            <?php
            if (isset($_SESSION['codigo'])) {
                echo '<label for="codigo">Clave de ingreso:</label>';
                echo '<input type="text" name="codigo" value="' . $_SESSION['codigo'] . '" readonly>';
                echo ' Favor de copiar esta clave para futuros accesos';
            } else {
                echo '<label for="codigo">Clave de ingreso:</label>';
                echo '<input type="text" name="codigo" required>';
            }
            ?>
        </div>

        <div class="form-group">
            <input type="submit" name="enviar" value="Generar Script" class="btn-submit">
        </div>

        <?php if (isset($_SESSION['codigo'])) { ?>
            <div class="form-group">
                <a href="mikrotik-modulos/modulos/ia/index.php" class="btn-ia">Generar con IA</a>
            </div>
        <?php } ?>
    </form>
</div>

<?php include "pie_pag.php"; ?>

<!-- Estilos CSS -->
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
    }

    .form-container {
        background: #fff;
        padding: 2em;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        width: 80%;
        max-width: 600px;
        margin: 2em auto;
    }

    .form-container h3 {
        margin-bottom: 1em;
        font-size: 24px;
        color: #333;
    }

    .form-group {
        margin-bottom: 1.5em;
    }

    .form-group label {
        font-size: 16px;
        color: #333;
        margin-bottom: 0.5em;
        display: block;
    }

    .form-group select,
    .form-group input {
        width: 100%;
        padding: 0.8em;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
    }

    .form-group input[type="text"] {
        padding: 0.8em;
        background-color: #f9f9f9;
    }

    .form-group input[type="submit"] {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border: none;
        cursor: pointer;
        border-radius: 5px;
        padding: 1em;
        transition: background-color 0.3s;
    }

    .form-group input[type="submit"]:hover {
        background-color: #45a049;
    }

    .btn-ia {
        display: block;
        width: 100%;
        padding: 1em;
        background-color: #0d6efd;
        color: #fff;
        text-align: center;
        text-decoration: none;
        font-size: 18px;
        border-radius: 5px;
        box-sizing: border-box;
        transition: background-color 0.3s;
    }

    .btn-ia:hover {
        background-color: #0b5ed7;
    }

    .alert {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1em;
        margin-bottom: 2em;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }

    .payment-options {
        display: flex;
        justify-content: space-around;
        margin-top: 2em;
    }

    .payment-option {
        text-align: center;
        width: 45%;
    }

    .payment-option b {
        display: block;
        margin-bottom: 1em;
    }
</style>
