<?php
//include "encabezado.php"; 
include "config.php";
session_start();
if (isset($_SESSION['f_username']) && isset($_SESSION['f_password']) && isset($_SESSION['f_profile']) && isset($_SESSION['f_title']))

$usuarios = explode("|", $_SESSION['f_username']);
$passwors = explode("|", $_SESSION['f_password']);
$perfiles = $_SESSION['f_profile'];
$titulo = $_SESSION['f_title'];
$contacto = $_SESSION['f_contact'];

for ($i=0;$i<count($usuarios);$i++){
	$codigo=$codigo_ticket;
	$codigo=str_replace("%u_username%",$usuarios[$i],$codigo);
	$codigo=str_replace("%u_password%",$passwors[$i],$codigo);
	$codigo=str_replace("%u_actualProfileName%",$perfiles,$codigo);
	$codigo=str_replace("%u_titulo%",$titulo,$codigo);
	$codigo=str_replace("%u_contacto%",$contacto,$codigo);

	echo $codigo;
}


//echo $_SESSION['f_username']."-".$_SESSION['f_password'];
//%u_username%

?>