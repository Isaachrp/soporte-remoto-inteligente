<?php
// Finalmente, destruir la sesión.
  session_start();
  unset($_SESSION["codigo"]); 
  session_destroy();
  header('Location: index.php');
  exit;
?>