<?php 
//include "encabezado.php";
//include "config.php";
//include "codigos.php"; 
?>

<?php
$velocidad = array("128k","256k","512k","768k", "1M", "2M", "3M","4M", "5M", "6M", "7M", "8M", "9M", "10M", "20M", "30M", "40M", "50M", "60M", "70M", "80M", "90M", "100M");

/*
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
        
        /*echo '<td>Red para clientes <br><b>LAN </b>: <select name="lan" >';
        for ($i=0;$i<255;$i++)
        {
          $gws1 = "172.16.".$i.".1";
          echo '<option value="'.$gws1.'">'.$gws1.'</option>';
        } 
        echo '</select> <br> <input type="checkbox" name="dhcp" checked> DHCP server';*/

        echo '<td>';

        echo '<table>';
         echo '<tr><td>Direccion IP del cliente:</td><td><input type="Text" name="ip_cliente" value=""></td></tr>';

        echo '<tr><td>Velocidad de subida:</td><td><select name="vel_subida" >';
        for ($i=0;$i<23;$i++){echo '<option value="'.$velocidad[$i].'">'.$velocidad[$i].'</option>';}
        echo '</select></td></tr>';

        echo '<tr><td>Velocidad de bajada:</td><td><select name="vel_bajada" >';
        for ($i=0;$i<23;$i++){echo '<option value="'.$velocidad[$i].'">'.$velocidad[$i].'</option>';}
        echo '</select></td></tr>';

        $fecha_inicio=date('Y-m-d');
        echo '<tr><td>Fecha de Inicio:</td><td><input type="date" name="fecha_inicio" value="'.$fecha_inicio.'"></td></tr>';

        echo '<tr><td>Fecha de Vencimiento:</td><td><input type="date" name="fecha_vencimiento" value="'.$fecha_inicio.'"></td></tr>';

       /* echo '
<label for="inputBirthday" class="control-label">Fecha de Nacimiento</label>
<input name="birthday" type="date" class="form-control" id="birthday" value="<?php 
    if(isset($_SESSION["birthday_patient"])) {
        echo $_SESSION["birthday_patient"];
    }?>" required>
    ';*/

        /*echo '<tr><td>Fecha de Inicio:</td><td><select name="long_usuario" value="'.$fecha_inicio.'" >';
        for ($i=4;$i<=10;$i++){echo '<option value="'.$i.'">'.$i.'</option>';}
        echo '</select></td></tr>';*/

        

      echo '<tr><td colspan="2"><input type="checkbox" name="igual"> Usuario igual a password </td></tr>';
      echo '<tr><td>Plan:</td><td><select name="perfil" >';
        foreach ($aPerfiles as &$valor) {echo '<option value="'.$valor.'">'.$valor.'</option>';}
        echo '</select></td></tr>';

         echo '<tr><td>Contacto:</td><td><input type="Text" name="contacto" value="722 55 309 14"></td></tr>';

      echo '<tr><td colspan="2"><input type="Submit" name="aceptar" value="Generar tickets"></td></tr>';
        
        echo '</table>';

        echo '</td>';

        echo '<td ><IMG SRC="clientes.jpg" height="300"></td></tr>';
        echo '<tr><td colspan="3">';

        echo 'algo';
        echo '</td></tr>';
    
echo "</table>"
    ?>
    <br>
    
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