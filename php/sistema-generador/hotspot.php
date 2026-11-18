<?php 
//include "encabezado.php";
//include "config.php";
//include "codigos.php"; 
?>

<?php
$velocidad = array("256k/512k", "512k/1M", "512k/2M", "512k/3M","512k/4M", "512k/5M", "512k/6M", "512k/7M", "512k/8M", "512k/9M", "512k/10M");
/*
session_start();
if (isset($_POST['codigo']) && buscarcod2($_POST['codigo']) )
{
  if (!isset($_SESSION['codigo']))
    $_SESSION['codigo'] = $_POST['codigo'];
 $_SESSION['tipo'] = $_POST['tipo'];
 $_SESSION['lineas'] = $_POST['lineas'];
 //echo  "si entra =".$_SESSION['codigo']."<br>";
} 
else
{
 
    header('Location: basica.php?error=cod');
  
  
}

echo "<h4 align='right'>Sesion iniciada: ".$_SESSION['codigo']." <a href='cerrar.php' name='modificar'>Cerrar</a></h4>";

 */
if ($_POST['enviar']){
  $lineas  = $_POST['lineas']; 
  $tipo  = $_POST['tipo']; 
  //echo "<h3><b>Basica ".$tipo."</b> <a href='basica.php?error=mod' name='modificar'>----Modificar parametros</a></h3><hr>";

  if ($lineas>=2){ ?>

    <form method="post" action="aplicar.php">
    <?php   
    echo '<input type="hidden" name="lineas" value="'.$lineas.'">';
    echo '<input type="hidden" name="tipo" value="'.$tipo.'">';
    echo "<table bgcolor='#ffffff' border='1' bordercolor='#dfdfdf' cellspacing='5' rules='rows'>"; 

   
      
      //echo '';
      echo ' <tr><td><IMG SRC="red.jpg" height="200"></td>';

        //echo '<td><IMG SRC="linea.jpg" height="100"></td>';

     
        //echo '<td > <IMG SRC="mikrotik.jpg" height="300">  </td>';
        //echo '<td rowspan='.$lineas.'>LAN:<input type="Text" name="lan"><br></td></tr>';
        
        echo '<td>Red para clientes <br><b>LAN </b>: <select name="lan" >';
        for ($i=0;$i<255;$i++)
        {
          $gws1 = "172.16.".$i.".1";
          echo '<option value="'.$gws1.'">'.$gws1.'</option>';
        } 
        echo '</select> <br> <input type="checkbox" name="dhcp" checked> DHCP server';

        

        echo '</td>';
        echo '<td ><IMG SRC="clientes.jpg" height="300"></td></tr>';
        echo '<tr><td colspan="3">';

        echo '<br><br><b>Elige planes: </b><br>';
        echo '<table border="1" rules="cols" bordercolor="#dfdfdf"><tr>';
        echo '<td><input type="checkbox" name="Plan1Hora" checked> Plan 1 Hora<br>'; 
        echo '<select name="vPlan1Hora" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan2Horas" checked> Plan 2 Horas <br>';
        echo '<select name="vPlan2Horas" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan4Horas" checked> Plan 4 Horas <br>';
        echo '<select name="vPlan4Horas" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan1Dia" checked> Plan un Dia <br>';
        echo '<select name="vPlan1Dia" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan1Semana" checked> Plan una Semana <br>';
        echo '<select name="vPlan1Semana" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan15Dias" checked> Plan 15 Dias <br>';
        echo '<select name="vPlan15Dias" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '<td><input type="checkbox" name="Plan30Dias" checked> Plan 30 Dias <br>';
        echo '<select name="vPlan30Dias" >';
        foreach ($velocidad as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';} 
        echo '</select> </td>';

        echo '</tr></table>';
        echo '</td></tr>';
    
echo "</table>"
    ?>
    <br>
    <input type="Submit" name="aceptar" value="Generar script">
    </form>
    <?php
  }
  else
  {
    echo "No puede realizar el balanceo";
  }
}

?>

<?php include "pie_pag.php" ?>