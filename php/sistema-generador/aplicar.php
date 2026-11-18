<?php
// Validate ECMP before presentation or legacy session parameter loops.
if (($_POST['tipo'] ?? '') === 'ECMP' && isset($_POST['aceptar'])) {
    require_once __DIR__ . '/lib/ecmp-contract.php';
    try {
        $n = filter_var($_POST['lineas'] ?? null, FILTER_VALIDATE_INT);
        if ($n === false || $n < 2 || $n > 12) throw new InvalidArgumentException();
        $validated = ['tipo'=>'ECMP', 'lineas'=>$n, 'lan'=>$_POST['lan'] ?? '', 'dhcp'=>!empty($_POST['dhcp'])];
        for ($i=1; $i<=$n; $i++) {
            $validated['vel'.$i] = $_POST['vel'.$i] ?? '';
            $validated['gw'.$i] = $_POST['gw'.$i] ?? '';
            $validated['ip'.$i] = filter_var($_POST['ip'.$i] ?? null, FILTER_VALIDATE_INT);
        }
        validate_ecmp($validated);
    } catch (Throwable $e) {
        http_response_code(422); echo 'Parametros ECMP invalidos.'; exit;
    }
}
include "encabezado.php";
      include "config.php";

?>
<?php 
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
if (!isset($_SESSION['codigo']))
    header('Location: index.php?error=cod');


echo "<h4 align='right'>Sesion iniciada: ".$_SESSION['codigo']." <a href='cerrar.php' name='modificar'>Cerrar</a></h4>";

if (isset($_POST['aceptar']) && $_POST['aceptar'] && isset($_SESSION['codigo'])){
  if (isset($_POST['lan']))
    $lan = $_POST['lan'];
  else
    $lan ="";
  $seg_lan=explode(".",$lan);
  if (isset($_POST['lineas']))
    $lineas  = $_POST['lineas']; 
  else
    $lineas  = "";
  if (isset($_POST['tipo']))
    $tipo  = $_POST['tipo']; 
  else
    $tipo  = ""; 
  //Inicializa variables de session
  if ($tipo!="Hotspot" && $tipo!="Tickets" && $tipo!="Firewall" && $tipo!="Residenciales")
  {
  for ($j=1;$j<=$lineas;$j++)
  {
   $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;

    $_SESSION[$velocidad]=$_POST[$velocidad] ?? "";
    $_SESSION[$gateway]=$_POST[$gateway] ?? "";
    $_SESSION[$ips]= $_POST[$ips] ?? ""; 
  }
}

  $script_ecmp="";
  $dns=array("8.8.8.8","8.8.4.4","208.67.222.222","208.67.220.220","1.1.1.1","1.0.0.1","64.6.64.6","64.6.65.6","8.26.56.26","8.20.247.20","89.233.43.71","9.9.9.9");
  echo "<h3><b>Script ".$tipo."</b><a href='index.php?error=mod' name='modificar'>----Modificar parametros</a></h3>";
  
  if ($tipo=="Tickets")
    echo "<h4><b>Tickets para imprimir</b><a href='imprimir.php' name='imprimir' target='_blank'>Ver</a></h4>";


  echo "<table align='center' bgcolor='#ffffff' border='1' bordercolor='#dfdfdf' cellspacing='8' cellpadding='8' rules='none'><tr><td>";
  if ($tipo=="Tickets") {
    if (isset($_POST['numero']))
      $numero  = $_POST['numero']; 
    else
      $numero=0;
  if (isset($_POST['prefijo']))
      $prefijo  = $_POST['prefijo']; 
    else
      $prefijo="";
    if (isset($_POST['long_usuario']))
       $longitud_u  = $_POST['long_usuario']; 
    else
       $longitud_u=4;

     if (isset($_POST['long_password']))
       $longitud_p  = $_POST['long_password']; 
    else
       $longitud_p=4;

    if (isset($_POST['perfil']))
       $perfil  = $_POST['perfil']; 
    else
       $perfil="default";    
     if (isset($_POST['titulo']))
       $titulo  = $_POST['titulo']; 
    else
       $titulo="Wifi por tiempo";   

     if (isset($_POST['contacto']))
       $contacto  = $_POST['contacto']; 
    else
       $contacto="";  

      $script_ecmp="<br>/ip hotspot user<br>";
    
    if ($perfil=="Plan1Hora")
      $f_profile="1h";
    else
    if ($perfil=="Plan2Horas")
      $f_profile="2h";
    else
    if ($perfil=="Plan4Horas")
      $f_profile="4h";
    else
      $f_profile="";

    $_SESSION['f_password']="";
    $_SESSION['f_username']="";
    $_SESSION['f_profile']=$perfil;
    $_SESSION['f_title']=$titulo;
    $_SESSION['f_contact']=$contacto;

    for ($i=0;$i<$numero;$i++)
    {
      if (isset($_POST['igual']) && $_POST['igual']){
        $t_Usuario=$prefijo.getRandomCode($longitud_u);
        $t_Password=$t_Usuario;
      }
      else{
        $t_Usuario=$prefijo.getRandomCode($longitud_u);
        $t_Password=getRandomCode($longitud_p);
      }
    $_SESSION['f_username']=$_SESSION['f_username'].$t_Usuario."|";
    $_SESSION['f_password']=$_SESSION['f_password'].$t_Password."|";

    if ($f_profile!="")
      $script_ecmp = $script_ecmp."add name=".$t_Usuario." password=".$t_Password." profile=".$perfil." limit-uptime=".$f_profile."<br>";
    else
      $script_ecmp = $script_ecmp."add name=".$t_Usuario." password=".$t_Password." profile=".$perfil."<br>";

    }

  }

  if ($tipo=="Residenciales")
  {
    $ip_cliente = $_POST['ip_cliente'] ?? '';
    $vel_subida = $_POST['vel_subida'] ?? '1M';
    $vel_bajada = $_POST['vel_bajada'] ?? '1M';
    $fecha_inicio = $_POST['fecha_inicio'] ?? '';
    $fecha_vencimiento = $_POST['fecha_vencimiento'] ?? '';
    $perfil = $_POST['perfil'] ?? '';
    $contacto = $_POST['contacto'] ?? '';

    if ($ip_cliente == '') {
      $script_ecmp = "Debe indicar la direccion IP del cliente.<br>";
    } else {
      $comentario = "Inicio: ".$fecha_inicio." Vence: ".$fecha_vencimiento." Perfil: ".$perfil." Contacto: ".$contacto;

      $script_ecmp = "<br>/queue simple<br>";
      $script_ecmp = $script_ecmp."add name=Cliente_".$ip_cliente." target=".$ip_cliente." max-limit=".$vel_subida."/".$vel_bajada." comment=\"".$comentario."\"<br>";
    }
  }
  else
   if ($tipo=="Hotspot")
  {


    
  $script_ecmp="<br>/interface ethernet<br>";
  $script_ecmp = $script_ecmp.'set [ find default-name=ether1 ] comment="Puerto 1:Internet" name=WAN<br>';
  $script_ecmp = $script_ecmp.'set [ find default-name=ether2 ] comment="Puerto 2:Hotspot" name=LAN<br>';

  $script_ecmp= $script_ecmp."<br>/ip hotspot profile<br>";
  $script_ecmp= $script_ecmp."add dns-name=wifi.hotspot.net hotspot-address=".$lan." html-directory=hotspot name=hsprof1<br>";

  $script_ecmp= $script_ecmp."<br>/ip hotspot<br>";
  $script_ecmp= $script_ecmp."add disabled=no interface=LAN name=hotspot1 profile=hsprof1<br>";

  $script_ecmp= $script_ecmp."<br>/ip address<br>";
  $script_ecmp= $script_ecmp."add address=".$lan."/24 interface=LAN network=172.16.".$seg_lan[2].".0<br>";

  $script_ecmp= $script_ecmp."<br>/ip dhcp-client<br>";
  $script_ecmp= $script_ecmp."add default-route-distance=0 dhcp-options=hostname,clientid disabled=no interface=WAN<br>";

  $script_ecmp= $script_ecmp."<br>/ip dns<br>"; 
  $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=".$lan.",8.8.8.8,8.8.4.4<br>";

  $script_ecmp= $script_ecmp."<br>/ip firewall nat<br>";
  $script_ecmp= $script_ecmp."add action=masquerade chain=srcnat out-interface=WAN<br>";

  

  $script_ecmp= $script_ecmp."<br>/ip hotspot user<br>";
  $script_ecmp= $script_ecmp."add name=admin password=12345<br>";

 

    
    
    // dhcp server
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250<br>";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."<br>";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan."<br>";
    }

    

    if (isset($_POST['Plan1Hora']) && $_POST['Plan1Hora']){
      
      $cad_perfil=str_replace("%dias%","0",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","1",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan1Hora",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan1Hora'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";
    }
    if (isset($_POST['Plan2Horas']) && $_POST['Plan2Horas']){
      
      $cad_perfil=str_replace("%dias%","0",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","2",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan2Horas",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan2Horas'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";
    }
    if (isset($_POST['Plan4Horas']) && $_POST['Plan4Horas']){
      
      $cad_perfil=str_replace("%dias%","0",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","4",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan4Horas",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan4Horas'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";
    }
    if (isset($_POST['Plan1Dia']) && $_POST['Plan1Dia']){
      $cad_perfil=str_replace("%dias%","1",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","0",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan1Dia",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan1Dia'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";

    }
     if (isset($_POST['Plan1Semana']) && $_POST['Plan1Semana']){
      $cad_perfil=str_replace("%dias%","7",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","0",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan1Semana",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan1Semana'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";

    }
    if (isset($_POST['Plan15Dias']) && $_POST['Plan15Dias']){
      $cad_perfil=str_replace("%dias%","15",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","0",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan15Dias",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan15Dias'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";

    }
    if (isset($_POST['Plan30Dias']) && $_POST['Plan30Dias']){
      $cad_perfil=str_replace("%dias%","30",$scrip_perfil);
      $cad_perfil=str_replace("%horas%","0",$cad_perfil);
      $cad_perfil=str_replace("%minutos%","0",$cad_perfil);
      $cad_perfil=str_replace("%nombre%","Plan30Dias",$cad_perfil);
      $cad_perfil=str_replace("%velocidad%",$_POST['vPlan30Dias'],$cad_perfil);
      $script_ecmp= $script_ecmp."<br>".$cad_perfil."<br>";

    }

    //echo "Minimo= ".$minimo."<br>";

  }
  elseif ($tipo=="PCC-DYNAMIC")
  { 
      // ============================================================
      // CONFIGURACION WAN
      // ============================================================

      $wanDefaults = array();
      $wanNames = array();
      $wanComments = array();
      $wanAddress = array();
      $wanNetwork = array();
      $wanBroadcast = array();
      $wanGateway = array();

      // Un anchor por WAN
      $wanAnchorIP = array(
          "8.8.8.8",
          "8.8.4.4",
          "1.1.1.1",
          "1.0.0.1",
          "9.9.9.9",
          "149.112.112.112",
          "208.67.222.222",
          "208.67.220.220",
          "76.76.19.19",
          "76.223.122.150",
          "94.140.14.14",
          "94.140.15.15"
      );

      for ($j=1; $j<=$lineas; $j++)
      {
          $gw = $_POST["gw".$j];
          $ip = $_POST["ip".$j];

          // Obtener tercer octeto del gateway
          $seg_gw = explode(".", $gw);
          $red = $seg_gw[2];

          $wanDefaults[] = "ether".$j;
          $wanNames[] = "WAN".$j;
          $wanComments[] = "Puerto ".$j;

          $wanAddress[] = "192.168.".$red.".".$ip."/24";
          $wanNetwork[] = "192.168.".$red.".0";
          $wanBroadcast[] = "192.168.".$red.".255";
          $wanGateway[] = $gw;
      }


      // ============================================================
      // CONFIGURACION LAN
      // ============================================================

      $seg_lan = explode(".", $lan);
      $lan_red = $seg_lan[2];

      $lanDefault   = "ether".($lineas + 1);
      $lanName      = "LAN";
      $lanComment   = "Puerto ".($lineas + 1);
      $lanAddress   = $lan."/24";
      $langw        = $lan;
      $lanNetwork   = "172.16.".$lan_red.".0";
      $lanBroadcast = "172.16.".$lan_red.".255";
      $lanPoolRange = "172.16.".$lan_red.".50-172.16.".$lan_red.".250";
      $dnsServers   = "8.8.8.8,8.8.4.4";


      // ============================================================
      // CONSTRUIR SCRIPT ROUTEROS
      // ============================================================

      $script_pcc_dynamic = "";

      // ---------------- CONFIGURACION WAN ----------------

      $script_pcc_dynamic .= "# ---------------- CONFIGURACION WAN ----------------\n";
      $script_pcc_dynamic .= "# Un elemento por cada WAN, en el mismo orden.\n";

      $script_pcc_dynamic .= ':global wanDefaults {"'
          .implode('";"', $wanDefaults)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanNames {"'
          .implode('";"', $wanNames)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanComments {"'
          .implode('";"', $wanComments)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanAddress {"'
          .implode('";"', $wanAddress)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanNetwork {"'
          .implode('";"', $wanNetwork)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanBroadcast {"'
          .implode('";"', $wanBroadcast)
          .'"}'."\n";

      $script_pcc_dynamic .= ':global wanGateway {"'
          .implode('";"', $wanGateway)
          .'"}'."\n";

      $script_pcc_dynamic .= '# IP publica "ancla" usada para resolver el gateway recursivo (una por WAN)'."\n";

      $script_pcc_dynamic .= ':global wanAnchorIP {"'
          .implode('";"', array_slice($wanAnchorIP, 0, $lineas))
          .'"}'."\n\n";


      // ---------------- CONFIGURACION LAN ----------------

      $script_pcc_dynamic .= "# ---------------- CONFIGURACION LAN (unica) ----------------\n";

      $script_pcc_dynamic .= ':global lanDefault "'.$lanDefault.'"'."\n";
      $script_pcc_dynamic .= ':global lanName "'.$lanName.'"'."\n";
      $script_pcc_dynamic .= ':global lanComment "'.$lanComment.'"'."\n";
      $script_pcc_dynamic .= ':global lanAddress "'.$lanAddress.'"'."\n";
      $script_pcc_dynamic .= ':global langw "'.$langw.'"'."\n";
      $script_pcc_dynamic .= ':global lanNetwork "'.$lanNetwork.'"'."\n";
      $script_pcc_dynamic .= ':global lanBroadcast "'.$lanBroadcast.'"'."\n";
      $script_pcc_dynamic .= ':global lanPoolRange "'.$lanPoolRange.'"'."\n";
      $script_pcc_dynamic .= ':global dnsServers "'.$dnsServers.'"'."\n\n";


      // ============================================================
      // NO EDITAR DE AQUI EN ADELANTE
      // ============================================================

      $script_pcc_dynamic .= "# ============================================================\n";
      $script_pcc_dynamic .= "# NO EDITAR DE AQUI EN ADELANTE\n";
      $script_pcc_dynamic .= "# ============================================================\n\n";

      $script_pcc_dynamic .= ':global wanCount [:len $wanDefaults]'."\n\n";


      // ============================================================
      // INTERFACES
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- INTERFACES ----------------\n";
      $script_pcc_dynamic .= "/interface ethernet\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local def ($wanDefaults->$i)'."\n";
      $script_pcc_dynamic .= '  :local nm  ($wanNames->$i)'."\n";
      $script_pcc_dynamic .= '  :local cm  ($wanComments->$i)'."\n";
      $script_pcc_dynamic .= '  set [ find default-name=$def ] comment=$cm name=$nm'."\n";
      $script_pcc_dynamic .= "}\n";

      $script_pcc_dynamic .= 'set [ find default-name=$lanDefault ] comment=$lanComment name=$lanName'."\n\n";


      // ============================================================
      // IP ADDRESS
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- IP ADDRESS ----------------\n";
      $script_pcc_dynamic .= "/ip address\n";

      $script_pcc_dynamic .= ':if ([:len [find address=$lanAddress interface=$lanName]] = 0) do={'."\n";
      $script_pcc_dynamic .= '  add address=$lanAddress interface=$lanName'."\n";
      $script_pcc_dynamic .= "}\n\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local addr ($wanAddress->$i)'."\n";
      $script_pcc_dynamic .= '  :local net  ($wanNetwork->$i)'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find address=$addr interface=($wanNames->$i)]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add address=$addr network="$net" interface=($wanNames->$i)'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // LIMPIEZA NAT
      // ============================================================

      $script_pcc_dynamic .= "# -----LIMPIEZA NAT GENERADO POR PCC-DYNAMIC-----\n\n";
      $script_pcc_dynamic .= "/ip firewall nat\n";
      $script_pcc_dynamic .= 'remove [find comment="PCC-DYNAMIC"]'."\n\n";


      // ============================================================
      // NAT
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- NAT ----------------\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local nm ($wanNames->$i)'."\n";
      $script_pcc_dynamic .= '  add chain=srcnat out-interface=$nm action=masquerade \\'."\n";
      $script_pcc_dynamic .= '    comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // ROUTING TABLES
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- ROUTING TABLES ----------------\n";
      $script_pcc_dynamic .= "/routing table\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local rt ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find name=$rt]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add disabled=no fib name=$rt'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // LIMPIEZA MANGLE
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- LIMPIEZA MANGLE ----------------\n";
      $script_pcc_dynamic .= "/ip firewall mangle\n"; 
      $script_pcc_dynamic .= 'remove [find comment="PCC-DYNAMIC"]'."\n\n";


      // ============================================================
      // MANGLE
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- MANGLE ----------------\n";
      $script_pcc_dynamic .= "/ip firewall mangle\n\n";

      // Accept redes WAN
      $script_pcc_dynamic .= "# accept a subredes de cada WAN local\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local net ($wanNetwork->$i)'."\n";
      $script_pcc_dynamic .= '  :local dstNet ($net . "/24")'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find chain=prerouting dst-address=$dstNet action=accept in-interface=$lanName]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add chain=prerouting dst-address=$dstNet action=accept in-interface=$lanName \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // Trafico entrante
      $script_pcc_dynamic .= "# marca de conexion para trafico entrante por cada WAN\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local nm  ($wanNames->$i)'."\n";
      $script_pcc_dynamic .= '  :local cmk ("wan" . ($i+1) . "_conn")'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find chain=prerouting in-interface=$nm connection-mark=no-mark new-connection-mark=$cmk]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add chain=prerouting in-interface=$nm connection-mark=no-mark action=mark-connection new-connection-mark=$cmk \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // PCC
      $script_pcc_dynamic .= "# PCC: reparte conexiones nuevas desde LAN entre las N WAN\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '  :local pccMethod ("both-addresses:" . $wanCount . "/" . $i)'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find chain=prerouting in-interface=$lanName connection-mark=no-mark per-connection-classifier=$pccMethod]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add chain=prerouting in-interface=$lanName connection-mark=no-mark dst-address-type=!local \\'."\n";
      $script_pcc_dynamic .= '      per-connection-classifier=$pccMethod action=mark-connection new-connection-mark=$cmk \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // Mark routing prerouting
      $script_pcc_dynamic .= "# mark-routing en prerouting (trafico reenviado desde LAN)\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '  :local rt  ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find chain=prerouting connection-mark=$cmk in-interface=$lanName action=mark-routing]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add chain=prerouting connection-mark=$cmk in-interface=$lanName action=mark-routing new-routing-mark=$rt \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // Mark routing output
      $script_pcc_dynamic .= "# mark-routing en output (trafico generado por el propio router)\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '  :local rt  ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find chain=output connection-mark=$cmk action=mark-routing]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add chain=output connection-mark=$cmk action=mark-routing new-routing-mark=$rt \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // RUTAS
      // ============================================================

      $script_pcc_dynamic .= "# ============================================================\n";
      $script_pcc_dynamic .= "# LIMPIEZA DE RUTAS GENERADAS POR PCC-DYNAMIC\n";
      $script_pcc_dynamic .= "# ============================================================\n\n";

      $script_pcc_dynamic .= "/ip route\n";
      $script_pcc_dynamic .= 'remove [find comment="PCC-DYNAMIC"]'."\n\n";

      $script_pcc_dynamic .= "# ---------------- IP ROUTE ----------------\n\n";

      // Rutas ancla
      $script_pcc_dynamic .= "# rutas ancla (scope 10) para resolver el gateway recursivo\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local anchor ($wanAnchorIP->$i)'."\n";
      $script_pcc_dynamic .= '  :local gw     ($wanGateway->$i)'."\n";
      $script_pcc_dynamic .= '  :local dstA   ($anchor . "/32")'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find dst-address=$dstA gateway=$gw scope=10]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add dst-address=$dstA distance=1 gateway=$gw scope=10 check-gateway=ping \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // Default por routing table
      $script_pcc_dynamic .= "# default por cada routing-table (balanceo)\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local anchor ($wanAnchorIP->$i)'."\n";
      $script_pcc_dynamic .= '  :local rt     ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find dst-address=0.0.0.0/0 gateway=$anchor routing-table=$rt target-scope=11]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add dst-address=0.0.0.0/0 gateway=$anchor routing-table=$rt target-scope=11 check-gateway=ping \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // Main
      $script_pcc_dynamic .= "# default en tabla principal (failover, distancia = orden de WAN)\n";

      $script_pcc_dynamic .= ':for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '  :local anchor ($wanAnchorIP->$i)'."\n";
      $script_pcc_dynamic .= '  :local dist   ($i+1)'."\n";

      $script_pcc_dynamic .= '  :if ([:len [find dst-address=0.0.0.0/0 distance=$dist gateway=$anchor target-scope=11 routing-table=main]] = 0) do={'."\n";
      $script_pcc_dynamic .= '    add dst-address=0.0.0.0/0 distance=$dist gateway=$anchor target-scope=11 check-gateway=ping \\'."\n";
      $script_pcc_dynamic .= '      comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "  }\n";
      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // DNS
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- DNS ----------------\n";
      $script_pcc_dynamic .= "/ip dns\n";
      $script_pcc_dynamic .= 'set allow-remote-requests=yes servers=$dnsServers'."\n\n";


      // ============================================================
      // DHCP
      // ============================================================

      if (isset($_POST['dhcpdinamico']) && $_POST['dhcpdinamico']) {
        $script_pcc_dynamic .= "# ---------------- POOL / DHCP (una sola LAN) ----------------\n";

        $script_pcc_dynamic .= "/ip pool\n";
        $script_pcc_dynamic .= ':if ([:len [find name=dhcp_pool_LAN]] = 0) do={'."\n";
        $script_pcc_dynamic .= '  add name=dhcp_pool_LAN ranges=$lanPoolRange'."\n";
        $script_pcc_dynamic .= "}\n\n";

        $script_pcc_dynamic .= "/ip dhcp-server\n";
        $script_pcc_dynamic .= ':if ([:len [find name=dhcp_LAN]] = 0) do={'."\n";
        $script_pcc_dynamic .= '  add address-pool=dhcp_pool_LAN disabled=no interface=$lanName lease-time=8h name=dhcp_LAN'."\n";
        $script_pcc_dynamic .= "}\n\n";

        $script_pcc_dynamic .= "/ip dhcp-server network\n";
        $script_pcc_dynamic .= ':if ([:len [find address=($lanNetwork . "/24")]] = 0) do={'."\n";
        $script_pcc_dynamic .= '  add address=($lanNetwork . "/24") dns-server=($langw . "," . $dnsServers) gateway=$langw'."\n";
        $script_pcc_dynamic .= "}\n\n";
      }


      // ============================================================
      // PCC-DYNAMIC MONITOR
      // ============================================================

      $script_pcc_dynamic .= "# ---------------- PCC-DYNAMIC ----------------\n";
      $script_pcc_dynamic .= "/system script\n";
      $script_pcc_dynamic .= 'remove [find name=PCC-DYNAMIC]'."\n\n";

      $script_pcc_dynamic .= "add name=PCC-DYNAMIC source={\n\n";

      $script_pcc_dynamic .= "    :global previousState\n\n";

      $script_pcc_dynamic .= '    :if ([:typeof $previousState] = "nothing") do={'."\n";
      $script_pcc_dynamic .= '        :set previousState ""'."\n";
      $script_pcc_dynamic .= "    }\n\n";

      $script_pcc_dynamic .= "    :global wanCount\n";
      $script_pcc_dynamic .= "    :global wanNames\n";
      $script_pcc_dynamic .= "    :global wanAnchorIP\n";
      $script_pcc_dynamic .= "    :global wanNetwork\n";
      $script_pcc_dynamic .= "    :global lanName\n\n";

      $script_pcc_dynamic .= '    :local anchorCount [:len $wanAnchorIP]'."\n\n";

      $script_pcc_dynamic .= '    :if ($wanCount != $anchorCount) do={'."\n\n";
      $script_pcc_dynamic .= '        :log error ("PCC-TEST: ERROR - WAN = " . $wanCount . " ANCLAS = " . $anchorCount)'."\n";
      $script_pcc_dynamic .= '        :error "Anchors doesn\'t match"'."\n";
      $script_pcc_dynamic .= "    }\n\n";

      $script_pcc_dynamic .= "    :local activeCount 0\n";
      $script_pcc_dynamic .= '    :local currentState ""'."\n";
      $script_pcc_dynamic .= '    :local changeDetected false'."\n\n";


      // Detección WAN
      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n\n";

      $script_pcc_dynamic .= '        :local wanName ($wanNames->$i)'."\n";
      $script_pcc_dynamic .= '        :local anchor ($wanAnchorIP->$i)'."\n\n";

      $script_pcc_dynamic .= '        :local active false'."\n\n";

      $script_pcc_dynamic .= '        :local wanId [/interface find name=$wanName]'."\n\n";

      $script_pcc_dynamic .= '        :if ([:len $wanId] = 0) do={'."\n\n";
      $script_pcc_dynamic .= '            :log warning ("PCC-TEST: " . $wanName . " NO EXISTE")'."\n\n";

      $script_pcc_dynamic .= "        } else={\n\n";

      $script_pcc_dynamic .= '            :local disabled [/interface get $wanId value-name=disabled]'."\n\n";

      $script_pcc_dynamic .= '            :if ($disabled = true) do={'."\n\n";
      $script_pcc_dynamic .= '                :log warning ("PCC-TEST: " . $wanName . " DESHABILITADA")'."\n\n";

      $script_pcc_dynamic .= "            } else={\n\n";

      $script_pcc_dynamic .= '                :local running [/interface get $wanId value-name=running]'."\n\n";

      $script_pcc_dynamic .= '                :if ($running = false) do={'."\n\n";
      $script_pcc_dynamic .= '                    :log warning ("PCC-TEST: " . $wanName . " SIN LINK")'."\n\n";

      $script_pcc_dynamic .= "                } else={\n\n";

      $script_pcc_dynamic .= '                    :local pingResult [/ping address=$anchor interface=$wanName count=3]'."\n\n";

      $script_pcc_dynamic .= '                    :if ($pingResult = 0) do={'."\n\n";
      $script_pcc_dynamic .= '                        :log warning ("PCC-TEST: " . $wanName . " SIN INTERNET")'."\n\n";

      $script_pcc_dynamic .= "                    } else={\n\n";

      $script_pcc_dynamic .= '                        :set active true'."\n\n";
      $script_pcc_dynamic .= '                        :log info ("PCC-TEST: " . $wanName . " INTERNET OK - " . $pingResult . "/3")'."\n";

      $script_pcc_dynamic .= "                    }\n";
      $script_pcc_dynamic .= "                }\n";
      $script_pcc_dynamic .= "            }\n";
      $script_pcc_dynamic .= "        }\n\n";


      $script_pcc_dynamic .= '        :if ($active = true) do={'."\n";
      $script_pcc_dynamic .= '            :set activeCount ($activeCount + 1)'."\n";
      $script_pcc_dynamic .= '            :set currentState ($currentState . "Y")'."\n";
      $script_pcc_dynamic .= "        } else={\n";
      $script_pcc_dynamic .= '            :set currentState ($currentState . "N")'."\n";
      $script_pcc_dynamic .= '            :log warning ("PCC-TEST: " . $wanName . " = INACTIVA")'."\n";
      $script_pcc_dynamic .= "        }\n\n";

      $script_pcc_dynamic .= "    }\n\n";


      // Estado
      $script_pcc_dynamic .= '    :log info ("PCC-TEST: WAN ACTIVAS = " . $activeCount)'."\n";
      $script_pcc_dynamic .= '    :log info ("PCC-TEST: ESTADO = " . $currentState)'."\n\n";

      $script_pcc_dynamic .= '    :if ($previousState = "") do={'."\n";
      $script_pcc_dynamic .= '        :set changeDetected true'."\n";
      $script_pcc_dynamic .= '        :log info "PCC-TEST: PRIMERA EJECUCION"'."\n";

      $script_pcc_dynamic .= "    } else={\n";
      $script_pcc_dynamic .= '        :if ($currentState = $previousState) do={'."\n";
      $script_pcc_dynamic .= '            :log info "PCC-TEST: SIN CAMBIOS"'."\n";

      $script_pcc_dynamic .= "        } else={\n";
      $script_pcc_dynamic .= '            :set changeDetected true'."\n";
      $script_pcc_dynamic .= '            :log warning ("PCC-TEST: CAMBIO DETECTADO " . $previousState . " -> " . $currentState)'."\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";

      $script_pcc_dynamic .= '    :if ($changeDetected = true) do={'."\n";
      $script_pcc_dynamic .= '        :log warning "PCC-TEST: CAMBIO = SI"'."\n";
      $script_pcc_dynamic .= "    } else={\n";
      $script_pcc_dynamic .= '        :log info "PCC-TEST: CAMBIO = NO"'."\n";
      $script_pcc_dynamic .= "    }\n\n";

      $script_pcc_dynamic .= '    :set previousState $currentState'."\n\n";


      // ============================================================
      // LIMPIAR MANGLE Y NAT
      // ============================================================

      $script_pcc_dynamic .= "    # ============================================================\n";
      $script_pcc_dynamic .= "    # CREAR MANGLE Y NAT SOLO PARA WAN ACTIVAS\n";
      $script_pcc_dynamic .= "    # ============================================================\n\n";

      $script_pcc_dynamic .= "    # ------------------------------------------------------------\n";
      $script_pcc_dynamic .= "    # LIMPIAR REGLAS ANTERIORES\n";
      $script_pcc_dynamic .= "    # ------------------------------------------------------------\n\n";

      $script_pcc_dynamic .= "    /ip firewall mangle\n";
      $script_pcc_dynamic .= '    remove [find comment="PCC-DYNAMIC"]'."\n\n";

      $script_pcc_dynamic .= "    /ip firewall nat\n";
      $script_pcc_dynamic .= '    remove [find comment="PCC-DYNAMIC"]'."\n\n";


      // ============================================================
      // CREAR MANGLE
      // ============================================================

      $script_pcc_dynamic .= "    # ============================================================\n";
      $script_pcc_dynamic .= "    # CREAR REGLAS MANGLE\n";
      $script_pcc_dynamic .= "    # ============================================================\n\n";

      $script_pcc_dynamic .= "    /ip firewall mangle\n\n";

      // Accept redes WAN activas
      $script_pcc_dynamic .= "    # accept a la red local de cada WAN\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";
      $script_pcc_dynamic .= '            :local net ($wanNetwork->$i)'."\n";
      $script_pcc_dynamic .= '            :local dstNet ($net . "/24")'."\n";

      $script_pcc_dynamic .= '            :if ([:len [find chain=prerouting dst-address=$dstNet action=accept in-interface=$lanName]] = 0) do={'."\n";
      $script_pcc_dynamic .= '                add chain=prerouting dst-address=$dstNet action=accept in-interface=$lanName \\'."\n";
      $script_pcc_dynamic .= '                  comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "            }\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";


      // Trafico entrante
      $script_pcc_dynamic .= "    # marca de conexion para trafico entrante por cada WAN\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";

      $script_pcc_dynamic .= '            :local nm  ($wanNames->$i)'."\n";
      $script_pcc_dynamic .= '            :local cmk ("wan" . ($i+1) . "_conn")'."\n";

      $script_pcc_dynamic .= '            :if ([:len [find chain=prerouting in-interface=$nm connection-mark=no-mark new-connection-mark=$cmk]] = 0) do={'."\n";
      $script_pcc_dynamic .= '                add chain=prerouting in-interface=$nm connection-mark=no-mark action=mark-connection new-connection-mark=$cmk \\'."\n";
      $script_pcc_dynamic .= '                  comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "            }\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";


      // PCC activo
      $script_pcc_dynamic .= "    # PCC: reparte conexiones nuevas desde LAN entre las WAN activas\n";
      $script_pcc_dynamic .= "    :local slot 0\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";

      $script_pcc_dynamic .= '            :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '            :local pccMethod ("both-addresses:" . $activeCount . "/" . $slot)'."\n";

      $script_pcc_dynamic .= '            :if ([:len [find chain=prerouting in-interface=$lanName connection-mark=no-mark per-connection-classifier=$pccMethod]] = 0) do={'."\n";
      $script_pcc_dynamic .= '                add chain=prerouting in-interface=$lanName connection-mark=no-mark dst-address-type=!local \\'."\n";
      $script_pcc_dynamic .= '                  per-connection-classifier=$pccMethod action=mark-connection new-connection-mark=$cmk \\'."\n";
      $script_pcc_dynamic .= '                  comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "            }\n";

      $script_pcc_dynamic .= '            :set slot ($slot + 1)'."\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";


      // Mark routing prerouting
      $script_pcc_dynamic .= "    # mark-routing en prerouting (trafico reenviado desde LAN)\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";

      $script_pcc_dynamic .= '            :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '            :local rt  ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '            :if ([:len [find chain=prerouting connection-mark=$cmk in-interface=$lanName action=mark-routing]] = 0) do={'."\n";
      $script_pcc_dynamic .= '                add chain=prerouting connection-mark=$cmk in-interface=$lanName action=mark-routing new-routing-mark=$rt \\'."\n";
      $script_pcc_dynamic .= '                  comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "            }\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";


      // Mark routing output
      $script_pcc_dynamic .= "    # mark-routing en output (trafico generado por el propio router)\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount - 1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";

      $script_pcc_dynamic .= '            :local cmk ("wan" . ($i+1) . "_conn")'."\n";
      $script_pcc_dynamic .= '            :local rt  ("to_wan" . ($i+1))'."\n";

      $script_pcc_dynamic .= '            :if ([:len [find chain=output connection-mark=$cmk action=mark-routing]] = 0) do={'."\n";
      $script_pcc_dynamic .= '                add chain=output connection-mark=$cmk action=mark-routing new-routing-mark=$rt \\'."\n";
      $script_pcc_dynamic .= '                  comment="PCC-DYNAMIC"'."\n";
      $script_pcc_dynamic .= "            }\n";
      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n\n";


      // ============================================================
      // NAT ACTIVO
      // ============================================================

      $script_pcc_dynamic .= "    # ---------------- NAT ----------------\n";
      $script_pcc_dynamic .= "    /ip firewall nat\n";

      $script_pcc_dynamic .= '    :for i from=0 to=($wanCount-1) do={'."\n";
      $script_pcc_dynamic .= '        :local state [:pick $currentState $i ($i + 1)]'."\n";

      $script_pcc_dynamic .= '        :if ($state = "Y") do={'."\n";
      $script_pcc_dynamic .= '            :local nm ($wanNames->$i)'."\n";

      $script_pcc_dynamic .= '            add chain=srcnat out-interface=$nm action=masquerade \\'."\n";
      $script_pcc_dynamic .= '              comment="PCC-DYNAMIC"'."\n";

      $script_pcc_dynamic .= "        }\n";
      $script_pcc_dynamic .= "    }\n";

      $script_pcc_dynamic .= "}\n\n";


      // ============================================================
      // SCHEDULER
      // ============================================================

      $script_pcc_dynamic .= "/system scheduler\n";
      $script_pcc_dynamic .= 'remove [find on-event=PCC-DYNAMIC]'."\n";

      $script_pcc_dynamic .= "/system scheduler add \\\n";
      $script_pcc_dynamic .= '    name="EjecutarBalanceoDinamico" \\'."\n";
      $script_pcc_dynamic .= '    interval=1m \\'."\n";
      $script_pcc_dynamic .= '    start-time=startup \\'."\n";
      $script_pcc_dynamic .= '    on-event="PCC-DYNAMIC"'."\n";


      // ============================================================
      // MOSTRAR SCRIPT GENERADO
      // ============================================================

      echo '<div style="display:flex; justify-content:flex-end; margin-bottom:8px;">';
      echo '<button type="button" onclick="copyScriptToClipboard(this, \'script-output-pcc\')" style="padding:6px 12px; border:1px solid #c7d2fe; border-radius:6px; background:#eef2ff; color:#1f2937; cursor:pointer; font-weight:bold;">Copiar script</button>';
      echo '</div>';
      echo '<pre id="script-output-pcc" style="white-space:pre-wrap; word-break:break-word; margin:0;">';
      echo htmlspecialchars($script_pcc_dynamic);
      echo "</pre>";
  }
  else
  if ($tipo=="ECMP") {
    require_once __DIR__ . "/lib/ecmp-legacy.php";
    $script_ecmp = legacy_ecmp($_POST);
  }
  else
    if ($tipo=="ECMPr")
  {
    

    $minimo=102400;
for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }

  
  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_input="";
  $script_output="";
  $script_route ="";
  $script_route_marck="";
  $script_recursivo="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_input = $script_input."add chain=input in-interface=WAN".$j." action=mark-connection new-connection-mark=wan".$j."_conn<br>";
    $script_output = $script_output."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=1 gateway=".$dns[$j-1]." routing-mark=to_wan".$j." check-gateway=ping<br>";
    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $proporcion[$j]=round($vel3[$j]/$minimo);
      for ($i=1;$i<=$proporcion[$j];$i++)
        if ($j!=$lineas)
          $script_route_marck= $script_route_marck.$dns[$j-1].",";
        else
          $script_route_marck= $script_route_marck.$dns[$j-1]." ";
    }
    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;
    
    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_input;
    $script_ecmp= $script_ecmp.$script_output;

    
    // Dns recursivo
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp."add dst-address=0.0.0.0/0 gateway=";
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp."check-gateway=ping<br>";
    $script_ecmp= $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }

    //echo "Minimo= ".$minimo."<br>";

  }
  else
    if ($tipo=="PCC")
  {

  $minimo=102400;
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
  $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=0;

   

  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting dst-address=192.168.".$seg[2].".0/24  action=accept in-interface=LAN<br>";
    $script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting in-interface=WAN".$j." connection-mark=no-mark action=mark-connection new-connection-mark=wan".$j."_conn<br>";
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting  in-interface=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses:".$packets."/".$pack." action=mark-connection new-connection-mark=wan".$j."_conn <br>";
        $pack++;
      }
    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting connection-mark=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_mangle_pre5 = $script_mangle_pre5."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$gw." routing-mark=to_wan".$j." check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." gateway=".$gw." check-gateway=ping<br>";
    }


    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre1;
    $script_ecmp= $script_ecmp.$script_mangle_pre2;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    $script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre5;
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }


  }
  else
    if ($tipo=="PCCr")
  {
    
   $minimo=102400;
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
  $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=0;

   

  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting dst-address=192.168.".$seg[2].".0/24  action=accept in-interface=LAN<br>";
    $script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting in-interface=WAN".$j." connection-mark=no-mark action=mark-connection new-connection-mark=wan".$j."_conn<br>";
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting  in-interface=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses:".$packets."/".$pack." action=mark-connection new-connection-mark=wan".$j."_conn <br>";
        $pack++;
      }
    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting connection-mark=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_mangle_pre5 = $script_mangle_pre5."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$dns[$j-1]." routing-mark=to_wan".$j." check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." gateway=".$dns[$j-1]." check-gateway=ping<br>";
    }


    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre1;
    $script_ecmp= $script_ecmp.$script_mangle_pre2;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    $script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre5;
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;


    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }
  }
else
    if ($tipo=="PCCrV7")
  {
    
   $minimo=102400;
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
  $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=0;

   

  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_routing_table ="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_routing_table = $script_routing_table."add disabled=no fib name=to_wan".$j."<br>";
    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting dst-address=192.168.".$seg[2].".0/24  action=accept in-interface=LAN<br>";
    $script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting in-interface=WAN".$j." connection-mark=no-mark action=mark-connection new-connection-mark=wan".$j."_conn<br>";
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting  in-interface=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses:".$packets."/".$pack." action=mark-connection new-connection-mark=wan".$j."_conn <br>";
        $pack++;
      }
    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting connection-mark=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_mangle_pre5 = $script_mangle_pre5."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$dns[$j-1]." routing-table=to_wan".$j." target-scope=11 check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." gateway=".$dns[$j-1]." target-scope=11 check-gateway=ping<br>";
    }


    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ routing table<br>";
    $script_ecmp= $script_ecmp.$script_routing_table;
    
    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre1;
    $script_ecmp= $script_ecmp.$script_mangle_pre2;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    $script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre5;
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;


    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }
  }
else
  if ($tipo=="PBr")
  {
    
   $minimo=102400;
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
  $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=0;

   

  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  
  $divisor=round(253/$lineas) - 1;
  $rango=1;

  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";

    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting dst-address=192.168.".$seg[2].".0/24  action=accept in-interface=LAN<br>";
    
    $suma = $rango+$divisor;

    $script_mangle_pre2 = $script_mangle_pre2."add address=172.16.".$seg_lan[2].".".$rango."-172.16.".$seg_lan[2].".".$suma."  list=to_wan".$j."<br>";
    $rango = $rango + $divisor + 1;

    //$script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting in-interface=WAN".$j." connection-mark=no-mark action=mark-connection new-connection-mark=wan".$j."_conn<br>";
    // /ip firewall address-list add address=192.168.6.248 list=Bloqueos
     /* $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting  in-interface=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses:".$packets."/".$pack." action=mark-connection new-connection-mark=wan".$j."_conn <br>";
        $pack++;
      }
add action=mark-routing chain=prerouting in-interface=LAN new-routing-mark=to_wan1 src-address-list=Bloqueos
      */
    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting  in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j." src-address-list=to_wan".$j." passthrough=no<br>";

   // $script_mangle_pre5 = $script_mangle_pre5."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$dns[$j-1]." routing-mark=to_wan".$j." check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." gateway=".$dns[$j-1]." check-gateway=ping<br>";
    }


    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;


    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall address-list<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre2;

    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre1;
    
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    $script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre5;
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;


    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }
  }
else
    if ($tipo=="PBrV7")
  {
    
   $minimo=102400;


  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
  $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=0;

   

  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_routing_table ="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";

  $divisor=round(253/$lineas) - 1;
  $rango=1;
  
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_routing_table = $script_routing_table."add disabled=no fib name=to_wan".$j."<br>";
    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting dst-address=192.168.".$seg[2].".0/24  action=accept in-interface=LAN<br>";
    //$script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting in-interface=WAN".$j." connection-mark=no-mark action=mark-connection new-connection-mark=wan".$j."_conn<br>";
    $suma = $rango+$divisor;

    $script_mangle_pre2 = $script_mangle_pre2."add address=172.16.".$seg_lan[2].".".$rango."-172.16.".$seg_lan[2].".".$suma."  list=to_wan".$j."<br>";
    $rango = $rango + $divisor + 1;

    /*  $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting  in-interface=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses:".$packets."/".$pack." action=mark-connection new-connection-mark=wan".$j."_conn <br>";
        $pack++;
      }*/

    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting  in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j." src-address-list=to_wan".$j." passthrough=no<br>";      
    //$script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting connection-mark=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=to_wan".$j."<br>";

   // $script_mangle_pre5 = $script_mangle_pre5."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$dns[$j-1]." routing-table=to_wan".$j." scope=11 check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." gateway=".$dns[$j-1]." check-gateway=ping<br>";
    }


    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall address-list<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre2;

    $script_ecmp= $script_ecmp."<br>/ routing table<br>";
    $script_ecmp= $script_ecmp.$script_routing_table;
    
    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    $script_ecmp= $script_ecmp.$script_mangle_pre1;
    //$script_ecmp= $script_ecmp.$script_mangle_pre2;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    $script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre5;
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;


    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }
  }
else
    if ($tipo=="NTH")
  {
   
    $minimo=102400;
for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
    $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=1;


   $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";

    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting src-address-list=wan".$j."_conn in-interface=LAN action=mark-connection new-connection-mark=wan".$j."_conn passthrough=yes <br>";
    $script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting src-address-list=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";
    $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting in-interface=LAN connection-state=new nth=".$packets.",".$pack." action=mark-connection new-connection-mark=wan".$j."_conn passthrough=yes<br>";
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";
        $pack++;
      }

    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn passthrough=yes<br>";

    //$script_mangle_pre5 = $script_mangle_pre5."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";

    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$gw." scope=255 target-scope=10 routing-mark=wan".$j."_conn check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." scope=255 target-scope=10 gateway=".$gw." check-gateway=ping<br>";
    }

    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp = $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    //$script_ecmp= $script_ecmp.$script_mangle_pre1;
   // $script_ecmp= $script_ecmp.$script_mangle_pre2;
    //$script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    //$script_ecmp= $script_ecmp.$script_mangle_pre4;
   
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }


  }
else
   if ($tipo=="Firewall")
  {
 
 /*




add action=drop chain=forward comment="Bloqueo DNS externo" disabled=yes \
    dst-port=53 in-interface-list=LANs protocol=udp



add action=accept chain=input comment="Reglas Basicas de Firewall" \
    connection-state=established,related
add action=drop chain=input connection-state=invalid
add action=accept chain=input src-address-list=LANs
add action=drop chain=input connection-nat-state=!dstnat
add action=accept chain=forward connection-state=established,related
add action=drop chain=forward connection-state=invalid
add action=accept chain=forward src-address-list=LANs
add action=drop chain=forward connection-nat-state=!dstnat

*/
/*
 $wan="WAN";
 $lan="192.168.10.0/24";
 $puertos_tcp="";
 $puertos_udp="";
 $lan_list="";
if (isset($_POST['wan']))
     $wan=$_POST['wan'];

if (isset($_POST['lan']))
     $lan=$_POST['lan'];
   $lans = explode("\n", $lan);

   for ($i=0;$i<count($lans);$i++){
      $lan_list=$lan_list."add address=".$lans[$i]." list=LANs<br>";
   }

   //print_r($lans);
   //echo "<br>";


if (isset($_POST['puertos_tcp']))
     $puertos_tcp=$_POST['puertos_tcp'];
if (isset($_POST['puertos_udp']))
     $puertos_udp=$_POST['puertos_udp'];

  $script_dns='add action=drop chain=input comment="Bloqueo DNS externo; no llegue al router" dst-port=53 in-interface='.$wan.' protocol=udp<br>';
  $script_dns=$script_dns.'add action=drop chain=forward comment="Bloqueo DNS externo: no pase a traves del router" disabled=yes dst-port=53 in-interface='.$wan.' protocol=udp<br>';

  $script_puertos='add action=accept chain=input dst-port='.$puertos_tcp.' protocol=tcp<br>';
  $script_puertos=$script_puertos.'add action=accept chain=input dst-port='.$puertos_udp.' protocol=udp<br>';

  $script_reglas='add action=accept chain=input comment="Reglas Basicas de Firewall" connection-state=established,related<br>';
  $script_reglas=$script_reglas.'add action=drop chain=input connection-state=invalid<br>';
  $script_reglas=$script_reglas.'add action=accept chain=input src-address-list=LANs<br>';
  $script_reglas=$script_reglas.'add action=drop chain=input connection-nat-state=!dstnat<br>';
  $script_reglas=$script_reglas.'add action=accept chain=forward connection-state=established,related<br>';
  $script_reglas=$script_reglas.'add action=drop chain=forward connection-state=invalid<br>';
  $script_reglas=$script_reglas.'add action=accept chain=forward src-address-list=LANs<br>';
  $script_reglas=$script_reglas.'add action=drop chain=forward connection-nat-state=!dstnat<br>';

   
  $script_firewall="/ip firewall address-list<br>"; 
  $script_firewall=$script_firewall.$lan_list.'<br>';
  //echo "Firewall".$wan;
  $script_firewall=$script_firewall."/ip firewall filter<br>";
  $script_firewall=$script_firewall.$script_dns;
  $script_firewall=$script_firewall.$script_puertos;
  $script_firewall=$script_firewall.$script_reglas;
  
  


  echo $script_firewall."<br>";*/

  $wan = $_POST['wan'] ?? "WAN";
$lan = $_POST['lan'] ?? "192.168.10.0/24";
$puertos_tcp = $_POST['puertos_tcp'] ?? "";
$puertos_udp = $_POST['puertos_udp'] ?? "";
$lan_list = "";

$lans = explode("\n", $lan);

// Generar lista de LANs
foreach ($lans as $lan_item) {
    $lan_list .= "add address={$lan_item} list=LANs<br>";
}

// Reglas DNS
$script_dns = [
    "add action=drop chain=input comment=\"Bloqueo DNS externo; no llegue al router\" dst-port=53 in-interface={$wan} protocol=udp",
    "add action=drop chain=forward comment=\"Bloqueo DNS externo: no pase a través del router\" disabled=yes dst-port=53 in-interface={$wan} protocol=udp"
];

// Reglas de puertos
$script_puertos = [];
if ($puertos_tcp) {
    $script_puertos[] = "add action=accept chain=input dst-port={$puertos_tcp} protocol=tcp";
}
if ($puertos_udp) {
    $script_puertos[] = "add action=accept chain=input dst-port={$puertos_udp} protocol=udp";
}

// Reglas básicas de firewall
$script_reglas = [
    "add action=accept chain=input comment=\"Reglas Básicas de Firewall\" connection-state=established,related",
    "add action=drop chain=input connection-state=invalid",
    "add action=accept chain=input src-address-list=LANs",
    "add action=drop chain=input connection-nat-state=!dstnat",
    "add action=accept chain=forward connection-state=established,related",
    "add action=drop chain=forward connection-state=invalid",
    "add action=accept chain=forward src-address-list=LANs",
    "add action=drop chain=forward connection-nat-state=!dstnat"
];

// Generar el script de firewall
$script_firewall = "/ip firewall address-list<br>{$lan_list}<br>/ip firewall filter<br>";

$script_firewall .= implode("<br>", $script_dns) . "<br>";
$script_firewall .= implode("<br>", $script_puertos) . "<br>";
$script_firewall .= implode("<br>", $script_reglas);

echo $script_firewall . "<br>";

  echo "</td></tr></table>";


  }
else
    if ($tipo=="NTHr")
  {
   
    $minimo=102400;
for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$_POST[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
    }
  //$script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
    $packets=0;
  for($j=1;$j<=$lineas;$j++)
    {
      $proporcion[$j]=round($vel3[$j]/$minimo);
      $packets=$packets + $proporcion[$j];
    } 
    
   $pack=1;


   $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_recursivo ="";
  $script_route ="";
  $script_route_marck="";
  $script_mangle_pre1="";
  $script_mangle_pre2="";
  $script_mangle_pre3="";
  $script_mangle_pre4="";
  $script_mangle_pre5="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$_POST[$velocidad];
    $gw=$_POST[$gateway];
    $ip= $_POST[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";

    $script_mangle_pre1 = $script_mangle_pre1."add chain=prerouting src-address-list=wan".$j."_conn in-interface=LAN action=mark-connection new-connection-mark=wan".$j."_conn passthrough=yes <br>";
    $script_mangle_pre2 = $script_mangle_pre2."add chain=prerouting src-address-list=wan".$j."_conn in-interface=LAN action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";
    $proporcion[$j]=round($vel3[$j]/$minimo);
      $j1=$j-1;
      for ($i=1;$i<=$proporcion[$j];$i++)
      {
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting in-interface=LAN connection-state=new nth=".$packets.",".$pack." action=mark-connection new-connection-mark=wan".$j."_conn passthrough=yes<br>";
        $script_mangle_pre3 = $script_mangle_pre3."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";
        $pack++;
      }

    $script_mangle_pre4 = $script_mangle_pre4."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn passthrough=yes<br>";

    //$script_mangle_pre5 = $script_mangle_pre5."add chain=prerouting in-interface=LAN connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=wan".$j."_conn passthrough=no<br>";

    $script_recursivo = $script_recursivo."add dst-address=".$dns[$j-1]." distance=1 gateway=".$gw." scope=10 check-gateway=ping<br>";
    $script_route_marck = $script_route_marck."add dst-address=0.0.0.0/0 gateway=".$dns[$j-1]." scope=255 target-scope=10 routing-mark=wan".$j."_conn check-gateway=ping<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=".$j." scope=255 target-scope=10 gateway=".$dns[$j-1]." check-gateway=ping<br>";

    }

    $script_ecmp="/interface ethernet<br>";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN<br>';

    $script_ecmp= $script_ecmp."<br>/ ip address<br>";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN<br>"; 
    $script_ecmp = $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."<br>/ ip firewall nat<br>";
    $script_ecmp= $script_ecmp.$script_nat;

    $script_ecmp= $script_ecmp."<br>/ ip firewall mangle<br>";
    //$script_ecmp= $script_ecmp.$script_mangle_pre1;
    //$script_ecmp= $script_ecmp.$script_mangle_pre2;
    //$script_ecmp= $script_ecmp.$script_mangle_pre4;
    $script_ecmp= $script_ecmp.$script_mangle_pre3;
    //$script_ecmp= $script_ecmp.$script_mangle_pre5;
   
    
    $script_ecmp= $script_ecmp."<br>/ ip route<br>";
    $script_ecmp= $script_ecmp.$script_recursivo;
    $script_ecmp= $script_ecmp.$script_route_marck;
    $script_ecmp= $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
 
    if (isset($_POST['dhcp']) && $_POST['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."<br>/ip pool<br>";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."<br>/ip dhcp-server<br>";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."<br>/ip dhcp-server network<br>";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }


  }
  
 echo '<div style="display:flex; justify-content:flex-end; margin-bottom:8px;">';
 echo '<button type="button" onclick="copyScriptToClipboard(this, \'script-output-general\')" style="padding:6px 12px; border:1px solid #c7d2fe; border-radius:6px; background:#eef2ff; color:#1f2937; cursor:pointer; font-weight:bold;">Copiar script</button>';
 echo '</div>';
 echo '<pre id="script-output-general" style="white-space:pre-wrap; word-break:break-word; margin:0;">';
 echo htmlspecialchars($script_ecmp);
 echo '</pre>';
 echo "</td></tr></table>";
 //</td></tr></table>
}
else
{
  $_SESSION['codigo'] = false;
  echo "Codigo incorrecto";
  header('Location: index.php?error=cod');
}
 
?>
<!-- Paso 1 -->
  <div class="step-container">
    <h4>Paso 1: Reset configuración</h4>
    <img src="/scripts/paso0.jpg" alt="Paso 1: Reset configuración">
  </div>

  <!-- Paso 2 -->
  <div class="step-container">
    <h4>Paso 2: Seleccionar y copiar Script</h4>
    <img src="/scripts/paso0.png" alt="Paso 2: Seleccionar y copiar Script">
  </div>

  <!-- Paso 3 -->
  <div class="step-container">
    <h4>Paso 3: Presionar clic derecho sobre New Terminal y en menú seleccionar pegar</h4>
    <img src="/scripts/paso2.jpg" alt="Paso 3: Presionar clic derecho sobre New Terminal">
  </div>

<script>
function copyScriptToClipboard(button, elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const text = el.innerText;
  navigator.clipboard.writeText(text).then(function() {
    const original = button.textContent;
    button.textContent = 'Copiado';
    setTimeout(function() {
      button.textContent = original;
    }, 1200);
  }).catch(function() {
    const temp = document.createElement('textarea');
    temp.value = text;
    temp.setAttribute('readonly', '');
    temp.style.position = 'fixed';
    temp.style.left = '-9999px';
    document.body.appendChild(temp);
    temp.select();
    document.execCommand('copy');
    document.body.removeChild(temp);
  });
}
</script>

<?php include "pie_pag.php" ?>
