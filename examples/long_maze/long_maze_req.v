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
  reg [4:0] state;
  assign error = 0;
  assign objective = state == 10;
  initial
  begin
    notfirst = 0;
    state = 0;
  end
    // # |6|   |
    // # | |1|2|
    // # |5|4|3|
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
      end else if (controllable_zone1 && state == 5) begin
        state <= 6;
      end else if (controllable_zone2 && state == 6) begin
        state <= 7;
      end else if (controllable_zone3 && state == 7) begin
        state <= 8;
      end else if (controllable_zone4 && state == 8) begin
        state <= 9;
      end else if (controllable_zone5 && state == 9) begin
        state <= 10;
      end else if (state == 11 || controllable_zone6) begin
        state <= 11;
      end else begin
        state <= state;
      end
    end
  end
endmodule
