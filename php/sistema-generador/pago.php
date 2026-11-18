<?php include "encabezado.php";
	  include "config.php";
?>
<?php if (isset($_SERVER['HTTP_REFERER']))
{
	//if (strpos($_SERVER['HTTP_REFERER'],"paypalobjects" ) || $_SERVER['HTTP_REFERER'],"paypal" ) || strpos($_SERVER['HTTP_REFERER'],"mercadopago" ) )
		
	//{

	$link = mysql_connect($hostname, $username, $password)
    or die('No se pudo conectar: ' . mysql_error());
	mysql_select_db($database) or die('No se pudo seleccionar la base de datos');
	$query = 'SELECT * FROM codigo WHERE uso="no"';
	$result = mysql_query($query) or die('Consulta fallida: ' . mysql_error());
	if ($line = mysql_fetch_array($result, MYSQL_ASSOC)) {
        echo "<h4>Su clave de ingreso es: ".$line['clave']."</h4>";    
        session_start();
        $_SESSION['codigo'] = $line['clave'];
        $clave=$_SESSION['codigo'];
        date_default_timezone_set('America/Mexico_City');
        $hoy = date("Y-m-d H:i:s");
        //$hoy = strtotime ( '-6 hour' , strtotime ( $hoy ) ) ;
        $query2 = 'UPDATE codigo SET uso="si", referencia="'.$_SERVER['HTTP_REFERER'].'", vencimiento="'.$hoy.'" WHERE clave="'.$clave.'"';
        mysql_query($query2) or die('Actualizacion fallida: ' . mysql_error());
		}
	mysql_free_result($result);
	mysql_close($link);

	header('Location: balanceo.php?error=no');

?>
<h4> Favor de copiar antes de cerrar esta ventana¡ Gracias por su preferencia !</h4>
<h4>Si tiene dudas contacte a:  info@mubu.com.mx o mensaje por whatsapp: 722 55 309 14</h4>
<a href='balanceo.php' name="Inicio"><b>Regresar al inicio</b></a>
<?php 
	//}
	}
else
{
?>
 <table border="1" rules="all" bordercolor="#bfbfbf">
            <tr><td colspan="2"><h4 color="red">Clave de ingreso incorrecto, debe aquirir una clave de ingreso, <br>durante la vigencia de su clave de ingreso puede generar todos los scripts que desee</h4></td></tr>
            <tr><td>
            <b>Paypal</b><br>
            <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
                <input type="hidden" name="cmd" value="_s-xclick">
                <input type="hidden" name="hosted_button_id" value="2WR9DQF2GGAKL">
                <table>
                <tr><td><input type="hidden" name="on0" value="Planes">Planes</td></tr><tr><td><select name="os0">
                <option value="1 Mes">1 Mes     $19.00 USD</option>
                <option value="2 Meses">2 Meses $29.00 USD</option>
                <option value="6 Meses">6 Meses $69.00 USD</option>
                <option value="1 Año">1 Año     $99.00 USD</option>
                </select> </td></tr>
                </table>
                <input type="hidden" name="currency_code" value="USD">
                <input type="image" src="https://www.paypalobjects.com/es_XC/MX/i/btn/btn_buynowCC_LG.gif" border="0" name="submit" alt="PayPal, la forma más segura y rápida de pagar en línea.">
                <img alt="" border="0" src="https://www.paypalobjects.com/es_XC/i/scr/pixel.gif" width="1" height="1">
            </form>


            </td><td>
            <b>MercadoPago, <br>Plan 1 Mes 399 pesos</b><br>
            <a mp-mode="dftl" href="https://www.mercadopago.com/mlm/checkout/start?pref_id=86218906-98417d55-82e7-43df-9c1e-6d81c516c381" name="MP-payButton" class='blue-ar-l-rn-none'>Pagar</a>
            <script type="text/javascript">
            (function(){function $MPC_load(){window.$MPC_loaded !== true && (function(){var s = document.createElement("script");s.type = "text/javascript";s.async = true;s.src = document.location.protocol+"//secure.mlstatic.com/mptools/render.js";var x = document.getElementsByTagName('script')[0];x.parentNode.insertBefore(s, x);window.$MPC_loaded = true;})();}window.$MPC_loaded !== true ? (window.attachEvent ?window.attachEvent('onload', $MPC_load) : window.addEventListener('load', $MPC_load, false)) : null;})();
            </script>
            </td></tr>
            <tr><td colspan="2">Otros metodos de pago favor de enviar correo a: info@mubu.com.mx o mensaje por whatsapp: 722 55 309 14</td></tr>

            </table>
<?php
}
?>

<?php include "pie_pag.php" ?>
