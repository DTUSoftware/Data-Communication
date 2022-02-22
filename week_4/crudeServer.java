import java.io.*;
import java.net.*;

class crudeServer {
   public static void main(String argv[]) throws Exception {
      ServerSocket mysocket = new ServerSocket(5558);
      System.out.println(" Server is Running  " );

      while (true) {
         Socket connectionSocket = mysocket.accept();

         BufferedReader reader = new BufferedReader(new  InputStreamReader(connectionSocket.getInputStream()));
         BufferedWriter writer=  new BufferedWriter(new OutputStreamWriter(connectionSocket.getOutputStream()));

         writer.write("*** Welcome to the Calculation Server (Addition Only) ***\n");
         writer.flush();
         writer.write("*** Please type in the first number and press Enter : \n");
         //writer.close();
         writer.flush();
         String data1 = reader.readLine();


         writer.write("*** Please type in the second number and press Enter : \n");
         //writer.close();
         writer.flush();
         String data2 = reader.readLine();

         int num1=Integer.parseInt(data1);
         int num2=Integer.parseInt(data2);

         int result=num1+num2;
         System.out.println("Addition operation done " );

         writer.write("=== Result is  : "+result);
         writer.flush();
         connectionSocket.close();
      }
   }
}
