`define k 5

// module main();
//     reg tb_lr;
//     reg tb_ud;
//     reg clk;
//     wire error, obj;
//     planning p(clk, tb_ud, tb_lr, error, obj);
//     initial begin
//         $dumpfile("test.vcd");
//         $dumpvars(0, main);
//         clk <= 0;
//         // up-left
//         tb_lr <= 0;
//         tb_ud <= 0;
//         toggle_clk;
//         // down-right
//         tb_lr <= 1;
//         tb_ud <= 1;
//         toggle_clk;
//         // up-right
//         tb_lr <= 1;
//         tb_ud <= 0;
//         toggle_clk;
//         toggle_clk;
//         // up-left
//         tb_lr <= 0;
//         tb_ud <= 0;
//         toggle_clk;
//         toggle_clk;
//     end
//     task toggle_clk;
//       begin
//         #10 clk = ~clk;
//         #10 clk = ~clk;
//       end
//     endtask        
// endmodule

module planning(input clk, 
                input updown,
                input controllable_leftright,
                output error,
                output objective);
  reg notfirst;
  reg [3:0] x;
  reg [3:0] y;

  assign error = (y == 2) && (x == 2);
  assign objective = x == 2;
  // assign error = (x == 2 && y == 2);
  // assign objective = x == 2;
  initial
  begin
    notfirst = 0;
    x = 0;
    y = 0;
  end
  always @(posedge clk)
  begin
    notfirst <= 1;
    if (!notfirst) begin
      x = 0;
      y = 2;
    end else if (x == 4 && y < 4) begin      
    end else begin
      if (~updown && y < `k-1) begin
        y <= y +1;
      end else if (updown && y >0 ) begin
        y <= y - 1;
      end
      if (~controllable_leftright && x>0) begin
        x <= x - 1;
      end else if (controllable_leftright && x < `k-1 ) begin
        x <= x + 1;
      end
    end
  end
endmodule
