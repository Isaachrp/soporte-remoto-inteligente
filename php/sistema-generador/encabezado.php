<html>

<!--script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-23626819-6', 'auto');
  ga('send', 'pageview');

</script-->
<head>
	<script language="JavaScript">
	function habilita(){
	valor = document.getElementById("tipo").value;
	valor=valor.trim();
	//alert(valor);
	if( valor == "Hotspot" || valor == "Tickets" ) {
		document.getElementById("lineas").style.visibility = "hidden";
		document.getElementById("text_lineas").style.visibility = "hidden";
	}
	else
	{
		document.getElementById("lineas").style.visibility = "visible";
		document.getElementById("text_lineas").style.visibility = "visible";
  	//alert(valor);
	}
}
</script>
<style>
  /* Estilo del contenedor del encabezado */
  .header {
    background-color: #ffffff;
    text-align: center;  /* Centra la imagen horizontalmente */
    padding: 20px 0;
  }

  /* Estilo de la imagen del logo */
  .logo {
    height: 100px;  /* Puedes cambiar el valor de 100px según el tamaño deseado */
  }
</style>
<style>
    /* Estilo base para el contenedor */
    .footer {
      background-color: #dfdfdf;
      padding: 20px;
      text-align: center;
      font-family: Arial, sans-serif;
    }
    
    /* Estilo para el texto de contacto */
    .footer h5 {
      margin: 0;
      color: #333;
      font-size: 16px;
    }

    /* Responsividad */
    @media (max-width: 600px) {
      .footer h5 {
        font-size: 14px;  /* Reducir el tamaño de la fuente en dispositivos pequeños */
      }
    }
  </style>
  <style>
    /* Estilo general */
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      margin: 0;
      padding: 0;
      background-color: #f4f4f4;
    }

    

    /* Contenedor para las imágenes y texto */
    .step-container {
      max-width: 800px;
      margin: 20px auto;
      padding: 15px;
      background-color: #fff;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }

    /* Estilo para las imágenes */
    .step-container img {
      width: 100%;
      height: auto;
      border-radius: 10px;
      margin-top: 10px;
    }

    /* Responsividad */
    @media (max-width: 768px) {
      h4 {
        font-size: 20px; /* Ajustar el tamaño del texto en pantallas más pequeñas */
      }
    }

    @media (max-width: 480px) {
      h4 {
        font-size: 18px; /* Ajustar aún más el tamaño del texto en pantallas muy pequeñas */
      }

      .step-container {
        padding: 10px;
      }
    }
  </style>

</head>
<body  >
<!--div style="margin:2px 10px 10px;"-->

<div class="header">
  <img src="/scripts/logo_b.png" alt="Logo" class="logo">
  <!-- Si quieres usar otra imagen de logo o cambiar el tamaño, puedes agregarla aquí -->
  <!-- <img src="balanceo3.jpg" alt="Otro Logo" class="logo"> -->
</div>
<div style="  padding: 1em;">
	