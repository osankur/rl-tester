module ring_req(input clk, 
                input loss,
                input reset,
                input controllable_stable,
                output error,
                output objective);
  reg first;
  reg [5:0] prg;
  reg stable;


  assign error = prg == `k-1 && ~stable;
  assign objective = prg == `k-1;
  initial
  begin
    first = 1;
    prg = 0;
    stable = 0;
  end
  always @(posedge clk)
  begin
    first <= 0;
    if (first) begin
      prg <= 0;
      stable <= 0;
    end else begin
      if (reset) begin
        prg <= 0;
      end else if (loss) begin
        prg <= prg;
      end
      else begin if (prg < `k-1)
        prg <= prg + 1;
        if (prg == `k-2) stable <= 1;
      end       
    end
  end
endmodule
