module main();
    reg tb_lr;
    reg tb_ud;
    reg clk;
    wire error, obj;
    reg olr, oud, z1, z2, z3, z4;
    long_maze_req p(clk, tb_ud, tb_lr, olr, oud, z1, z2, z3, z4, error, obj);
    initial begin
        $dumpfile("test.vcd");
        $dumpvars(0, main);
        clk <= 0;
        // up-left
        tb_lr <= 0;
        tb_ud <= 0;
        olr <= 1;
        oud <= 0;
        z1 <= 0;
        z2 <= 0;
        z3 <= 0;
        z4 <= 0;
        toggle_clk;


        // down-right
        tb_lr <= 1;
        tb_ud <= 1;
        z1 <= 1;
        toggle_clk;

        // up-right
        z1 <= 0;
        z2 <= 1;
        tb_lr <= 1;
        tb_ud <= 0;
        toggle_clk;
        z2 <= 0;
        z3 <= 1;
        toggle_clk;
        toggle_clk;
        toggle_clk;

        z3 <= 0;
        z4 <= 1;
        // up-left
        tb_lr <= 0;
        tb_ud <= 0;
        toggle_clk;
        toggle_clk;
    end
    task toggle_clk;
      begin
        #10 clk = ~clk;
        #10 clk = ~clk;
      end
    endtask        
endmodule

module long_maze_req(input clk, 
                input iupdown,
                input ileftright,
                // input controllable_oleftright,
                // input controllable_oupdown,
                input controllable_zone1,
                input controllable_zone2,
                input controllable_zone3,
                input controllable_zone4,
                input controllable_zone5,
                input controllable_zone6,
                output error,
                output objective);
  reg notfirst;
  reg [3:0] state;
  assign error = 0;
  assign objective = state == 5;
  initial
  begin
    notfirst = 0;
    state = 0;
  end
  always @(posedge clk)
  begin
    notfirst <= 1;
    if (!notfirst) begin
      state = 0;
    end else begin
      if (controllable_zone1 && state == 0) begin
        state <= 1;
      end else if (controllable_zone2 && state == 1) begin
        state <= 2;
      end else if (controllable_zone3 && state == 2) begin
        state <= 3;
      end else if (controllable_zone4 && state == 3) begin
        state <= 4;
      end else if (controllable_zone5 && state == 4) begin
        state <= 5;
      end else if (state == 6 || controllable_zone6) begin
        state <= 6;
      end else begin
        state <= state;
      end
    end
  end
endmodule
