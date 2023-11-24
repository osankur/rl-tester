module test();
    reg up;
    reg right;
    reg z0;
    reg z1;
    reg z2;
    reg z3;
    reg z4;
    reg z5;
    reg z6;
    reg z7;
    reg z8;
    reg z9;
    reg open;
    reg ds;
    reg clk;
    reg f;
    wire error, obj;
    corridor p(clk, up, right, z0, z1, z2, z3, z4, z5, z6, z7, z8, z9, open, ds, f, error, obj);
    initial begin
        $dumpfile("test.vcd");
        $dumpvars(0, test);
        clk <= 1;
        z1 <= 0;
        z2 <= 0;
        z3 <= 0;
        z4 <= 0;
        z5 <= 0;
        z6 <= 0;
        z7 <= 0;
        z8 <= 0;
        z9 <= 0;
        ds <= 0;
        open <= 0;
        f <=0;

        right <= 1; up <= 0;
        z0 <= 1;
        toggle_clk;

        right <= 1; up <= 1;
        toggle_clk;

        right <= 1; up <= 0;
        ds <= 1;
        toggle_clk;

        right <= 1; up <= 0;
        ds <= 1; open <= 1;
        toggle_clk;


// rollout
        right <= 1; up <= 0;
        ds <= 0; open <= 1;
        z0 <= 0; z1 <= 1;
        toggle_clk;

        right <= 0; up <= 0;
        ds <= 1; open <= 1;
        z0 <= 1; z1 <= 0;

        toggle_clk;
        right <= 0; up <= 1;
        ds <= 0; open <= 0;
        toggle_clk;
        f <= 1;
        toggle_clk;
        toggle_clk;
        toggle_clk;

        // up <= 0;
        // right <= 1;
        // z0 <=1;
        // z1 <= 0;
        // open <= 0;
        // ds <= 0;

        // toggle_clk;
        // open <= 1;
        // toggle_clk;
        // ds <= 1;
        // toggle_clk;
        // z0 <= 0;
        // z1 <= 0;
        // toggle_clk;
        // toggle_clk;
    end
    task toggle_clk;
      begin
        #10 clk = ~clk;
        #10 clk = ~clk;
      end
    endtask        
endmodule


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
                input controllable_zone4,
                input controllable_zone5,
                input controllable_zone6,
                input controllable_zone7,
                input controllable_zone8,
                input controllable_zone9,
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
  assign objective = notfirst && ~fault && ~err && (zone == 9);
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
        else if((zone == 2 && mode == 2 || zone == 4)  && controllable_zone3) zone <= 3;
        else if((zone == 3 && mode == 2 || zone == 5)  && controllable_zone4) zone <= 4;
        else if((zone == 4 && mode == 2 || zone == 6)  && controllable_zone5) zone <= 5;
        else if((zone == 5 && mode == 2 || zone == 7)  && controllable_zone6) zone <= 6;
        else if((zone == 6 && mode == 2 || zone == 8)  && controllable_zone7) zone <= 7;
        else if((zone == 7 && mode == 2 || zone == 9)  && controllable_zone8) zone <= 8;
        else if((zone == 8 && mode == 2)  && controllable_zone9) zone <= 9;
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
                    || zone == 4 && controllable_zone4
                    || zone == 5 && controllable_zone5
                    || zone == 6 && controllable_zone6
                    || zone == 7 && controllable_zone7
                    || zone == 8 && controllable_zone8
                    || zone == 9 && controllable_zone9
                )) begin
                //|| idown && ~controllable_open || iup && controllable_open) begin
                err <= 1;
            end  else err <= err;
            // if we go down-right, we stay in open, and may reach doorstep (cooperative step)
            // end else if (controllable_open && controllable_doorstep) begin
            //     err <= err;
            //     mode <= 2;
            //     zone <= zone;
            // end else if (controllable_open && ~controllable_doorstep) begin
            //     err <= err;
            //     mode <= mode;
            //     zone <= zone;
            // end else if (~controllable_open) begin
            //     mode <= 0;
            //     zone <= zone;
            //     err <= err;
            // end 
        // if door is open and at doorstep
        end else if (mode == 2) begin
            if ((zone == 0 && (iright && ~controllable_zone1 || ileft && controllable_zone1))
                || (zone == 1 && (iright && ~controllable_zone2 || ileft && controllable_zone2))
                || (zone == 2 && (iright && ~controllable_zone3 || ileft && controllable_zone3))
                || (zone == 3 && (iright && ~controllable_zone4 || ileft && controllable_zone4))
                || (zone == 4 && (iright && ~controllable_zone5 || ileft && controllable_zone5))
                || (zone == 5 && (iright && ~controllable_zone6 || ileft && controllable_zone6))
                || (zone == 6 && (iright && ~controllable_zone7 || ileft && controllable_zone7))
                || (zone == 7 && (iright && ~controllable_zone8 || ileft && controllable_zone8))
                || (zone == 8 && (iright && ~controllable_zone9 || ileft && controllable_zone9))
            ) err <= 1;
            else err <= err;
        end else begin
            err <= err;
        end
    end
  end
endmodule
