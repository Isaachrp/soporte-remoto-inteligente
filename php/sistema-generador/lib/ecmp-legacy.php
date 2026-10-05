<?php
function ecmp_text(array $input): string {
  $tipo="ECMP"; $lineas=$input["lineas"]; $lan=$input["lan"]; $seg_lan=explode(".",$lan);

    
  $minimo=102400;
for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $vel=$input[$velocidad];
    $vel1 = substr($vel, 0, strlen($vel)-1);
    $vel2= substr($vel, strlen($vel)-1);
   
    if ($vel2=="M")
      $vel3[$j]=$vel1*1024;
    else
      $vel3[$j]=$vel1;
    if ($minimo>$vel3[$j])
      $minimo=$vel3[$j];

    }
  
  $script_interface="";
  $script_wan="";
  $script_nat="";
  $script_input="";
  $script_output="";
  $script_route ="";
  $script_route_marck ="";
  for($j=1;$j<=$lineas;$j++)
    {
    $velocidad = "vel".$j;
    $gateway = "gw".$j;
    $ips = "ip".$j;
    $vel=$input[$velocidad];
    $gw=$input[$gateway];
    $ip= $input[$ips];
    $seg = explode(".", $gw);
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'
';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."
";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade
";
    $script_input = $script_input."add chain=input in-interface=WAN".$j." action=mark-connection new-connection-mark=wan".$j."_conn
";
    $script_output = $script_output."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."
";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=1 gateway=".$gw." routing-mark=to_wan".$j." check-gateway=ping
";
    $proporcion[$j]=round($vel3[$j]/$minimo);
      for ($i=1;$i<=$proporcion[$j];$i++)
        $script_route_marck= $script_route_marck.$gw.",";
    }

    $script_ecmp="/interface ethernet
";
    $script_ecmp = $script_ecmp.$script_interface;
    $script_ecmp = $script_ecmp.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=LAN
';

    $script_ecmp= $script_ecmp."
/ ip address
";
    $script_ecmp= $script_ecmp."add address=".$lan."/24 network=172.16.".$seg_lan[2].".0 broadcast=172.16.".$seg_lan[2].".255 interface=LAN
"; 
    $script_ecmp= $script_ecmp.$script_wan;

    $script_ecmp= $script_ecmp."
/ ip firewall nat
";
    $script_ecmp= $script_ecmp.$script_nat;
    
    $script_ecmp= $script_ecmp."
/ ip firewall mangle
";
    $script_ecmp= $script_ecmp.$script_input;
    $script_ecmp= $script_ecmp.$script_output;

    $script_ecmp= $script_ecmp."
/ ip route
add dst-address=0.0.0.0/0 gateway=";
    $script_ecmp= $script_ecmp.rtrim($script_route_marck, ',')." ";
  
    $script_ecmp= $script_ecmp."check-gateway=ping
";
    $script_ecmp = $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."
/ip dns
";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4
";
    
    // dhcp server
    if (isset($input['dhcp']) && $input['dhcp'])
    {
      $seg = explode(".", $lan);
      $script_ecmp= $script_ecmp."
/ip pool
";
      $script_ecmp= $script_ecmp."add name=dhcp_pool_".$tipo." ranges=172.16.".$seg[2].".50-172.16.".$seg[2].".250";
    
      $script_ecmp= $script_ecmp."
/ip dhcp-server
";
      $script_ecmp= $script_ecmp."add address-pool=dhcp_pool_".$tipo." disabled=no interface=LAN lease-time=8h name=dhcp_".$tipo."";

      $script_ecmp= $script_ecmp."
/ip dhcp-server network
";
      $script_ecmp= $script_ecmp."add address=172.16.".$seg[2].".0/24 dns-server=".$lan.",8.8.8.8,8.8.4.4 gateway=".$lan;
    }


  
return $script_ecmp;
}

function legacy_ecmp(array $input): string {
  return str_replace("\n", '<br>', ecmp_text($input));
}
