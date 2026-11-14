 // Check at settled physical clock edges, including disabled CPU cycles.
 reg r11_active=0,r11_writing=0;
 reg [23:0] r11_address;
 reg [7:0] r11_data;
 integer r11_held_edges=0;
 always @(posedge clk) begin
  if(!reset_n) begin r11_active=0;r11_writing=0;end
  else begin
   if(!io && a[23:16]!==8'h00) $fatal(1,"I/O or IACK escaped bank zero");
   if(!rf && a[23:16]!==8'h00) $fatal(1,"refresh escaped bank zero");
   if(r11_active && !mr && rf && a!==r11_address)
     $fatal(1,"request address changed before release old=%h new=%h",r11_address,a);
   if(r11_writing && !wr && dout!==r11_data)
     $fatal(1,"write payload changed before release");
   r11_active=!mr&&rf;r11_writing=!wr;
   r11_address=a;r11_data=dout;
   if(r11_active)r11_held_edges=r11_held_edges+1;
  end
 end
