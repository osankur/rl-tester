import java.net.*;
import java.io.*;

public class TxsAdapter implements Runnable {
    private int portNr;

    TxsAdapter(String portNrStr) {
        this.portNr = Integer.parseInt(portNrStr);
    }

    public void run() {
        startAdapter();
    }

    public static void main(String[] args) throws IOException {
        if (args.length == 0) {
            System.out.println("Own port number required");
            return;
        }
        // Start adders in parallel, one per-each port number.
        String msg = String.format("Starting %d processes.", args.length);
        System.out.println(msg);
        for (String arg : args) {
            (new Thread(new TxsAdapter(arg))).start();
        }
    }

    private void startAdapter() {
        System.out.println(String.format("Starting an adder listening on port %d", portNr));
        try {
            ServerSocket serverSock = new ServerSocket(portNr);
            Socket sock = serverSock.accept();

            InputStream inStream = sock.getInputStream();
            BufferedReader sockIn = new BufferedReader(new InputStreamReader(inStream));

            OutputStream outStream = sock.getOutputStream();
            PrintWriter sockOut = new PrintWriter(new OutputStreamWriter(outStream));

            final int maxSleepTime = 180;
            byte[] buffer = new byte[4000];

            ProcessBuilder builder = new ProcessBuilder("python3", "passageway.py", "-s");
            builder.redirectErrorStream(true); // so we can ignore the error stream
            Process process = builder.start();
            InputStream out = process.getInputStream();
            OutputStream in = process.getOutputStream();

            while (true) {
                // Get input from Torxakis
                String s = sockIn.readLine();
                if (s == null) {
                    continue;
                }
                s = s.trim();
                System.out.println(s);
                s = s + "\n";
                // Forward input to process
                byte[] sbytes = s.getBytes();
                in.write(sbytes, 0, sbytes.length);
                in.flush();

                int no = 0;
                while(no <= 0){
                    no = out.available();
                }
                int n = out.read(buffer, 0, Math.min(no, buffer.length));
                String msg = new String(buffer, 0, n);
                String [] parts = msg.split("\n",0);
                // assert(parts.length == 2);
                // for(String p : parts){
                //     System.out.println("part: " + p);
                // }

                // processInput(s, sockOut, maxSleepTime);
                
                // Forward output to Torxakis
                sockOut.print(parts[0]+"\n");
                sockOut.flush();
                System.out.println(parts[0]+"\n");
                System.out.println(parts[1]+"\n");

                // // Read state, and just print it
                // no = 0;
                // while(no <= 0){
                //     no = out.available();
                // }
                // n = out.read(buffer, 0, Math.min(no, buffer.length));
                // msg = new String(buffer, 0, n);
                // System.out.println("Ignoring: " + msg);


            }
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }
}
