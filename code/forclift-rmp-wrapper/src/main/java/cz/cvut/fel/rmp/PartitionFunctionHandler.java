package cz.cvut.fel.rmp;

import edu.ucla.cs.starai.forclift.inference.PartitionFunctionExact;
import edu.ucla.cs.starai.forclift.inference.WeightedCNF;
import edu.ucla.cs.starai.forclift.languages.mln.MLN;
import edu.ucla.cs.starai.forclift.languages.mln.MLNParser;
import edu.ucla.cs.starai.forclift.util.SignLogDouble;

import io.netty.channel.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

public class PartitionFunctionHandler extends SimpleChannelInboundHandler<String> { // (1)


    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String msg) throws Exception {
        if (msg.isEmpty()) {
            ctx.writeAndFlush("NO_FILE_GIVEN\n");
        } else if (msg.equalsIgnoreCase("CLOSE")) {
            ChannelFuture future = ctx.writeAndFlush("CLOSED\n");
            future.addListener(ChannelFutureListener.CLOSE);
        } else if (msg.equalsIgnoreCase("SHUTDOWN")){
            ChannelFuture future = ctx.writeAndFlush("SHUTTING_DOWN\n");
            future.addListener((fut) -> {
                assert fut == future;
                ctx.channel().close();
                ctx.channel().parent().close();
            });
        } else {
            try {
                double z = calculatePartitionFunction(msg);
                ctx.writeAndFlush(z + "\n");
            } catch (IOException e) {
                System.out.println(e.getMessage());
                ctx.writeAndFlush("CALC_ERR\n");
            }
        }
    }

    private double calculatePartitionFunction(String definitionFile) throws IOException {
        List<String> fileInput = Files.readAllLines(Paths.get(definitionFile));
        String fString = String.join("\n", fileInput);
        MLNParser mlnParser = new MLNParser();
        MLN mln = mlnParser.parseMLN(fString);
        WeightedCNF wCnf = mln.toWeightedCNF(false, true);
        PartitionFunctionExact pfe = new PartitionFunctionExact(false);
        SignLogDouble sld = pfe.computePartitionFunction(wCnf);
        return sld.toLogDouble();
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) throws Exception {
        cause.printStackTrace();
        if (ctx.channel().isOpen()) {
            ctx.writeAndFlush("ERR\n");
        }
    }
}
