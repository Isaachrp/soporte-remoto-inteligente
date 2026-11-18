
<?php 
include "encabezado.php";
include "config.php";
include "codigos.php"; 
session_start();
?>

<?php
if (isset($_POST['codigo']) && buscarcod($_POST['codigo'])) {
    if (!isset($_SESSION['codigo'])) {
        $_SESSION['codigo'] = $_POST['codigo'];
    }
    $_SESSION['tipo'] = $_POST['tipo'];
    $_SESSION['lineas'] = $_POST['lineas'];
} else {
    echo "Si entra aquí";
    header('Location: index.php?error=cod');
    exit;
}

echo "<h4 align='right' class='session-info'>Sesión iniciada: " . htmlspecialchars($_SESSION['codigo']) . " <a href='cerrar.php' class='logout'>Cerrar</a></h4>";

if (isset($_POST['enviar'])) {
    $lineas = (int)$_POST['lineas']; 
    $tipo = htmlspecialchars($_POST['tipo']);

    if ($tipo == "Hotspot") {
        echo "<h3 class='script-title'>Script " . $tipo . "</h3><hr>";
        include "hotspot.php";
    } elseif ($tipo == "Tickets") {
        echo "<h3 class='script-title'>Script " . $tipo . "</h3><hr>";
        include "tickets.php";
    } elseif ($tipo == "Residenciales") {
        echo "<h3 class='script-title'>Script " . $tipo . "</h3><hr>";
        include "residenciales.php";
    } elseif ($tipo == "Firewall") {
        echo "<h3 class='script-title'>Script " . $tipo . "</h3><hr>";
        include "firewall.php";
    } elseif ($tipo == "PCC-DYNAMIC") {
        echo "<h3 class='script-title'>Balanceo PCC Dinámico</h3><hr>";

        if ($lineas >= 2 && $lineas <= 12) {
            echo '<form method="post" action="aplicar.php" class="form-script">';
            echo '<input type="hidden" name="lineas" value="' . $lineas . '">';
            echo '<input type="hidden" name="tipo" value="' . $tipo . '">';
            echo "<table class='script-table'>";

            for ($j = 1; $j <= $lineas; $j++) {
                $gw = "gw" . $j;
                $ip = "ip" . $j;
                $wanDefault = "ether" . $j;

                echo '<tr><td><IMG SRC="modem.gif" height="80"></td>';
                echo '<td> WAN(' . $j . '): Interfaz: <input type="text" name="wanDefault' . $j . '" value="' . $wanDefault . '" readonly style="width:80px;"></td>';

                echo '<td>Gateway: <select name="' . $gw . '">';
                for ($i = 0; $i < 255; $i++) {
                    $gws1 = "192.168." . $i . ".1";
                    echo '<option value="' . $gws1 . '" ' . ($i == $j ? 'selected="selected"' : '') . '>' . $gws1 . '</option>';
                }
                for ($i = 0; $i < 255; $i++) {
                    $gws254 = "192.168." . $i . ".254";
                    echo '<option value="' . $gws254 . '">' . $gws254 . '</option>';
                }
                echo '</select></td>';

                echo '<td>IP: <select name="' . $ip . '">';
                for ($i = 2; $i < 254; $i++) {
                    echo '<option value="' . $i . '" ' . ($i == 2 ? 'selected="selected"' : '') . '>' . $i . '</option>';
                }
                echo '</select></td>';

                if ($j == 1) {
                    echo '<td rowspan="' . $lineas . '"><IMG SRC="mikrotik.jpg" height="300"></td>';
                    echo '<td rowspan="' . $lineas . '">Red para clientes <br><b>LAN </b>: <select name="lan">';
                    for ($i = 0; $i < 255; $i++) {
                        $gws1 = "172.16." . $i . ".1";
                        echo '<option value="' . $gws1 . '">' . $gws1 . '</option>';
                    }
                    echo '</select><br> <input type="checkbox" name="dhcpdinamico"> DHCP server</td>';
                    echo '<td rowspan="' . $lineas . '"><IMG SRC="clientes.jpg" height="300"></td></tr>';
                }
            }
            echo "</table>";
            echo '<br><input type="submit" name="aceptar" value="Generar script" class="submit-btn">';
            echo '</form>';
        } else {
            echo "No puede realizar el script";
        }
    } else {
        echo "<h3 class='script-title'>Balanceo " . $tipo . "</h3><hr>";

        if ($lineas >= 2) {
            echo '<form method="post" action="aplicar.php" class="form-script">';
            echo '<input type="hidden" name="lineas" value="' . $lineas . '">';
            echo '<input type="hidden" name="tipo" value="' . $tipo . '">';
            echo "<table class='script-table'>";
            
            for ($j = 1; $j <= $lineas; $j++) {
                $vel = "vel" . $j;
                $gw = "gw" . $j;
                $ip = "ip" . $j;
                
                echo '<tr><td><IMG SRC="modem.gif" height="80"></td>';
                echo '<td> WAN(' . $j . '): Velocidad: <select name="' . $vel . '"> 
                        <option value="256k">256k</option> 
                        <option value="512k">512k</option> 
                        <option value="1M">1M</option>
                        <option value="2M">2M</option>
                        <option value="3M">3M</option>
                        <option value="4M">4M</option>
                        <option value="5M" selected="selected">5M</option>
                        <option value="6M">6M</option>
                        <option value="7M">7M</option>
                        <option value="8M">8M</option>
                        <option value="9M">9M</option>
                        <option value="10M">10M</option>
                        <option value="15M">15M</option>
                        <option value="20M">20M</option>
                        <option value="30M">30M</option>
                        <option value="40M">40M</option>
                        <option value="50M">50M</option>
                        <option value="60M">60M</option>
                        <option value="70M">70M</option>
                        <option value="80M">80M</option>
                        <option value="90M">90M</option>
                        <option value="100M">100M</option>
                        <option value="150M">150M</option>
                        <option value="200M">200M</option>
                        <option value="250M">250M</option>
                        <option value="300M">300M</option>
                        <option value="350M">350M</option>
                        <option value="400M">400M</option>
                        <option value="450M">450M</option>
                        <option value="500M">500M</option>
                        <option value="550M">550M</option>
                        <option value="600M">600M</option>
                        <option value="650M">650M</option>
                        <option value="700M">700M</option>
                        <option value="750M">750M</option>
                        <option value="800M">800M</option>
                        <option value="850M">850M</option>
                        <option value="900M">900M</option>
                        <option value="950M">950M</option>
                        <option value="1000M">1000M</option>
                      </select></td>';
                
                // Gateway
                echo '<td>Gateway: <select name="' . $gw . '">';
                for ($i = 0; $i < 255; $i++) {
                    $gws1 = "192.168." . $i . ".1";
                    echo '<option value="' . $gws1 . '" ' . ($i == $j ? 'selected="selected"' : '') . '>' . $gws1 . '</option>';
                }
                for ($i = 0; $i < 255; $i++) {
                    $gws254 = "192.168." . $i . ".254";
                    echo '<option value="' . $gws254 . '">' . $gws254 . '</option>';
                }
                echo '</select></td>';
                
                // IP Address
                echo '<td>IP: <select name="' . $ip . '">';
                for ($i = 2; $i < 254; $i++) {
                    echo '<option value="' . $i . '" ' . ($i == 2 ? 'selected="selected"' : '') . '>' . $i . '</option>';
                }
                echo '</select></td>';
                
                if ($j == 1) {
                    echo '<td rowspan="' . $lineas . '"><IMG SRC="mikrotik.jpg" height="300"></td>';
                    echo '<td rowspan="' . $lineas . '">Red para clientes <br><b>LAN </b>: <select name="lan">';
                    for ($i = 0; $i < 255; $i++) {
                        $gws1 = "172.16." . $i . ".1";
                        echo '<option value="' . $gws1 . '">' . $gws1 . '</option>';
                    }
                    echo '</select><br> <input type="checkbox" name="dhcp"> DHCP server</td>';
                    echo '<td rowspan="' . $lineas . '"><IMG SRC="clientes.jpg" height="300"></td></tr>';
                }
            }
            echo "</table>";
            echo '<br><input type="submit" name="aceptar" value="Generar script" class="submit-btn">';
            echo '</form>';
        } else {
            echo "No puede realizar el script";
        }
    }
}
?>

<?php include "pie_pag.php"; ?>

<!-- CSS para el estilo -->
<style>
  body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    color: #333;
    margin: 0;
    padding: 0;
  }

  h4.session-info {
    font-size: 16px;
    background-color: #eee;
    padding: 10px;
    border-bottom: 1px solid #ddd;
  }

  h4.session-info a.logout {
    color: red;
    text-decoration: none;
  }

  .script-title {
    font-size: 24px;
    color: #333;
    font-weight: bold;
  }

  .form-script {
    margin: 20px auto;
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    max-width: 1000px;
    width: 90%;
  }

  .script-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
  }

  .script-table td {
    padding: 10px;
    text-align: center;
    border: 1px solid #ddd;
  }

  .submit-btn {
    background-color: #4CAF50;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
  }

  .submit-btn:hover {
    background-color: #45a049;
  }

  select {
    padding: 8px;
    margin: 5px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }

  input[type="checkbox"] {
    margin-top: 10px;
  }
</style>
