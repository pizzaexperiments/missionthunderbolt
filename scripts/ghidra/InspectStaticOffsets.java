// Inspect explicitly supplied private offsets; never infer semantic labels from constants alone.
// @category MissionThunderbolt
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

public class InspectStaticOffsets extends GhidraScript {
    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=2)throw new IllegalArgumentException("Expected private query TSV and private output directory");
        var match=Pattern.compile("CODE_([0-9]+)_[0-9]+\\.bin").matcher(currentProgram.getName());
        if(!match.matches())return;
        int segment=Integer.parseInt(match.group(1));
        List<String[]> queries=new ArrayList<>();List<String> input=Files.readAllLines(Path.of(args[0]));
        for(int i=1;i<input.size();++i) {
            String[] row=input.get(i).split("\t");
            if(row.length!=3 || !row[2].matches("[A-Za-z0-9_-]+"))throw new IllegalArgumentException("Malformed query");
            if(Integer.parseInt(row[0])==segment)queries.add(row);
        }
        if(queries.isEmpty())return;
        Path repo=Path.of(getSourceFile().getAbsolutePath()).toRealPath().getParent().getParent().getParent();
        Path requested=Path.of(args[1]).toAbsolutePath().normalize();
        if(requested.startsWith(repo) && !requested.startsWith(repo.resolve("local-generated")))
            throw new IllegalArgumentException("Keep original-derived evidence private");
        Path output=requested.resolve("CODE_"+segment);
        if(Files.exists(output))throw new IllegalArgumentException("Refusing to overwrite evidence");
        Files.createDirectories(output);
        List<String> report=new ArrayList<>();
        report.add("label\tsegment\tquery_offset\tinstruction_offset\tfunction_offset\tgenerated_name\tdecompile_status\terror");
        DecompInterface decompiler=new DecompInterface();
        try {
            boolean opened=decompiler.openProgram(currentProgram);
            for(String[] query:queries) {
                long offset=Long.parseLong(query[1]);var address=toAddr(offset);
                var instruction=currentProgram.getListing().getInstructionContaining(address);
                var function=instruction==null ? null : getFunctionContaining(instruction.getAddress());
                String instructionOffset=instruction==null?"":Long.toString(instruction.getAddress().getOffset());
                String functionOffset=function==null?"":Long.toString(function.getEntryPoint().getOffset());
                if(instruction!=null) {
                    List<String> nearby=new ArrayList<>();
                    var iterator=currentProgram.getListing().getInstructions(instruction.getAddress(),true);
                    for(int n=0;n<16 && iterator.hasNext();++n) {
                        var item=iterator.next();nearby.add(item.getAddress()+" "+item.toString());
                    }
                    Files.write(output.resolve(query[2]+"_"+offset+"_window.asm"),nearby);
                }
                String status="no-decoded-function",error="";
                if(function!=null && opened) {
                    var result=decompiler.decompileFunction(function,30,monitor);
                    if(result.decompileCompleted() && result.getDecompiledFunction()!=null) {
                        String code=result.getDecompiledFunction().getC();
                        status=code.contains("halt_baddata") || code.contains("Bad instruction") ? "partial-unverified" : "exported-unverified";
                        Files.writeString(output.resolve(query[2]+"_"+offset+".c"),"/* PRIVATE DECOMPILER HYPOTHESIS. Types/roles/runtime semantics unverified.\n * Segment "+segment+", query offset "+offset+", SHA256 "+currentProgram.getExecutableSHA256()+". */\n"+code);
                    } else {status="failed";error=result.getErrorMessage().replace('\t',' ').replace('\n',' ');}
                    List<String> window=new ArrayList<>();var iterator=currentProgram.getListing().getInstructions(function.getEntryPoint(),true);
                    for(int n=0;n<100 && iterator.hasNext();++n) {
                        var item=iterator.next();if(!function.getBody().contains(item.getAddress()))break;
                        window.add(item.getAddress()+" "+item.toString());
                    }
                    Files.write(output.resolve(query[2]+"_"+offset+".asm"),window);
                }
                report.add(query[2]+"\t"+segment+"\t"+offset+"\t"+instructionOffset+"\t"+functionOffset+"\t"+(function==null?"":function.getName())+"\t"+status+"\t"+error);
            }
        } finally {decompiler.dispose();}
        Files.write(output.resolve("queries.tsv"),report);
        println("Inspected "+queries.size()+" explicitly supplied offsets in CODE "+segment);
    }
}
