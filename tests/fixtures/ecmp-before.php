<?php
function legacy_ecmp(array $input): string {
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
    //echo "vel".$j. "=".$vel3[$j]." = ".$vel2."<br>";
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
    $script_interface = $script_interface.'set [ find default-name=ether'.$j.' ] comment="Puerto '.$j.'" name=WAN'.$j.'<br>';
    $script_wan = $script_wan."add address=192.168.".$seg[2].".".$ip."/24 network=192.168.".$seg[2].".0 broadcast=192.168.".$seg[2].".255 interface=WAN".$j."<br>";
    $script_nat = $script_nat."add chain=srcnat out-interface=WAN".$j." action=masquerade<br>";
    $script_input = $script_input."add chain=input in-interface=WAN".$j." action=mark-connection new-connection-mark=wan".$j."_conn<br>";
    $script_output = $script_output."add chain=output connection-mark=wan".$j."_conn action=mark-routing new-routing-mark=to_wan".$j."<br>";
    $script_route = $script_route."add dst-address=0.0.0.0/0 distance=1 gateway=".$gw." routing-mark=to_wan".$j." check-gateway=ping<br>";
    $proporcion[$j]=round($vel3[$j]/$minimo);
      for ($i=1;$i<=$proporcion[$j];$i++)
        if ($j!=$lineas)
          $script_route_marck= $script_route_marck.$gw.",";
        else
          $script_route_marck= $script_route_marck.$gw." ";
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

    $script_ecmp= $script_ecmp."<br>/ ip route<br>add dst-address=0.0.0.0/0 gateway=";
    $script_ecmp= $script_ecmp.$script_route_marck;
  
    $script_ecmp= $script_ecmp."check-gateway=ping<br>";
    $script_ecmp = $script_ecmp.$script_route;

    // dns servers
    $script_ecmp= $script_ecmp."<br>/ip dns<br>";
    $script_ecmp= $script_ecmp."set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4<br>";
    
    // dhcp server
    if (isset($input['dhcp']) && $input['dhcp'])
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

  
return $script_ecmp;
}
