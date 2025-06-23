

/**
Semantics:
At any state:
- iup, iright are provided (input to SUT)
- controllable_* are read (output of SUT)
- new state' reached

Here controllable_* are properties of state'.
*/
module corridor(input clk, 
                input iup,
                input iright,
                input controllable_zone0,
                input controllable_zone1,
                input controllable_zone2,
                input controllable_zone3,
                input controllable_open,
                input controllable_doorstep,
                input controllable_fault,
                output error,
                output objective);
  reg notfirst;
  reg[4:0] zone;  
  reg[2:0] mode; // 0: door not open, 1: door open, 2: doorstep and door open
  reg fault;
  reg err;
  wire ileft = ~iright;
  wire idown = ~iup;

  assign error =  err;
  assign objective = notfirst && ~fault && ~err && (zone == 3);
//   wire mode0 = ~controllable_open;
//   wire mode1 = controllable_open && ~controllable_doorstep;
//   wire mode2 = controllable_open && controllable_doorstep;
  initial
  begin
    notfirst = 0;
    zone = 0;
    err = 0;
    mode = 0;
    fault = 0;
  end
    // ____________
    // |        | |
    // |        |d|
    // |________|s|
    // |__open__|_|
  always @(posedge clk)
  begin
    notfirst <= 1;    
    if (!notfirst) begin
      zone <= 0;
      mode <= 0;
      err <= 0;
      fault <= 0;
    end else begin
        if (controllable_fault) fault <= 1;
        else fault <= fault;
        if(controllable_open && ~controllable_doorstep) mode <= 1;
        else if (controllable_open && controllable_doorstep) mode <= 2;
        else mode <= 0;
        if(controllable_zone0) zone <= 0;
        else if((zone == 0 && mode == 2 || zone == 2)  && controllable_zone1) zone <= 1;
        else if((zone == 1 && mode == 2 || zone == 3)  && controllable_zone2) zone <= 2;
        else if((zone == 2 && mode == 2)  && controllable_zone3) zone <= 3;
        else zone <= zone;

        // if door is not open
        if (mode == 0 ) begin 
            if (iup && controllable_open)  begin
                err <= 1;
            end else begin 
                err <= err;
            end
        // if door is open but not at doorstep
        end else if (mode == 1)begin
            // if we go left, we cannot reach doorstep; if go down, we must stay at open area; and if we go up, we must leave open
            if (
                ileft && controllable_doorstep && (
                    zone == 0 && controllable_zone0
                    || zone == 1 && controllable_zone1
                    || zone == 2 && controllable_zone2
                    || zone == 3 && controllable_zone3
                )) begin
                err <= 1;
            end  else err <= err;
        // if door is open and at doorstep
        end else if (mode == 2) begin
            if ((zone == 0 && (iright && ~controllable_zone1 || ileft && controllable_zone1))
                || (zone == 1 && (iright && ~controllable_zone2 || ileft && controllable_zone2))
                || (zone == 2 && (iright && ~controllable_zone3 || ileft && controllable_zone3))
            ) err <= 1;
            else err <= err;
        end else begin
            err <= err;
        end
    end
  end
endmodule
