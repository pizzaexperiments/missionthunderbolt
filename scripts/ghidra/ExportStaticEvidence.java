// Exact A-line references and private decompiler hypotheses, never original source.
// @category MissionThunderbolt
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import ghidra.program.model.address.Address;
import java.util.regex.Pattern;

public class ExportStaticEvidence extends GhidraScript {
    private static class Candidate {
        Function function;
        int score=0;
        List<String> names=new ArrayList<>();
        Candidate(Function f) {function=f;}
    }
    private int score(String names) {
        if(names.contains("_Random"))return 100;
        if(names.contains("Resource"))return 20;
        if(names.contains("NextEvent"))return 15;
        if(names.contains("DrawPicture") || names.contains("CopyBits"))return 10;
        return 0;
    }
    @Override
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=3)throw new IllegalArgumentException("Expected private trap TSV, private output directory, per-segment decompile limit");
        int limit=Integer.parseInt(args[2]);
        if(limit<0 || limit>32)throw new IllegalArgumentException("Decompile limit must be 0..32");
        var match=Pattern.compile("CODE_([0-9]+)_[0-9]+\\.bin").matcher(currentProgram.getName());
        if(!match.matches() || match.group(1).equals("0"))return;
        int segment=Integer.parseInt(match.group(1));
        Path repo=Path.of(getSourceFile().getAbsolutePath()).toRealPath().getParent().getParent().getParent();
        Path requested=Path.of(args[1]).toAbsolutePath().normalize();
        if(requested.startsWith(repo) && !requested.startsWith(repo.resolve("local-generated")))
            throw new IllegalArgumentException("Keep original-derived output under ignored local-generated/ or outside checkout");
        Path output=requested.resolve("CODE_"+segment);
        if(Files.exists(output))throw new IllegalArgumentException("Refusing to overwrite existing segment evidence");
        Map<Integer,String> reference=new HashMap<>();
        List<String> table=Files.readAllLines(Path.of(args[0]));
        for(int i=1;i<table.size();++i) {
            String[] row=table.get(i).split("\t",-1);
            if(row.length!=2)throw new IllegalArgumentException("Malformed trap reference");
            reference.put(Integer.parseInt(row[0]),row[1]);
        }
        List<String> traps=new ArrayList<>();
        traps.add("segment\tinstruction_offset\tfunction_offset\tword\treference_names\tcontext\tconfidence");
        Map<Long,Candidate> candidates=new HashMap<>();
        Map<Long,Address> sites=new TreeMap<>();
        Map<Long,Function> contextFunctions=new HashMap<>();
        Map<Long,String> contexts=new HashMap<>();
        var instructions=currentProgram.getListing().getInstructions(true);
        while(instructions.hasNext()) {
            Instruction instruction=instructions.next();byte[] bytes=instruction.getBytes();
            Function function=getFunctionContaining(instruction.getAddress());
            if(bytes.length==2 && ((bytes[0]&0xf0)==0xa0)) {
                long address=instruction.getAddress().getOffset();sites.put(address,instruction.getAddress());
                contexts.put(address,"decoded-instruction");if(function!=null)contextFunctions.put(address,function);
            }
            List<Address> next=new ArrayList<>();
            if(instruction.getFallThrough()!=null)next.add(instruction.getFallThrough());
            for(Address flow:instruction.getFlows())next.add(flow);
            for(Address address:next) {
                if(!currentProgram.getMemory().contains(address) || getInstructionAt(address)!=null)continue;
                if(currentProgram.getListing().getDefinedDataAt(address)!=null)continue;
                try {
                    int word=currentProgram.getMemory().getShort(address)&0xffff;
                    if((word&0xf000)!=0xa000)continue;
                    sites.put(address.getOffset(),address);
                    contexts.put(address.getOffset(),"undecoded-flow-frontier");
                    if(function!=null)contextFunctions.putIfAbsent(address.getOffset(),function);
                } catch(Exception ignored) { /* Boundary/truncation: not a site. */ }
            }
        }
        var functions=currentProgram.getFunctionManager().getFunctions(true);
        while(functions.hasNext()) {
            Function function=functions.next();Address address=function.getEntryPoint();
            if(getInstructionAt(address)!=null)continue;
            try {
                int word=currentProgram.getMemory().getShort(address)&0xffff;
                if((word&0xf000)!=0xa000)continue;
                sites.put(address.getOffset(),address);contexts.put(address.getOffset(),"undecoded-function-entry");
                contextFunctions.put(address.getOffset(),function);
            } catch(Exception ignored) { }
        }
        int known=0,unknown=0;
        for(var site:sites.entrySet()) {
            int word=currentProgram.getMemory().getShort(site.getValue())&0xffff;
            String names=reference.getOrDefault(word,"");
            if(names.isEmpty())unknown++;else known++;
            Function function=contextFunctions.get(site.getKey());
            String entry=function==null ? "" : Long.toString(function.getEntryPoint().getOffset());
            String context=contexts.get(site.getKey());
            traps.add(segment+"\t"+site.getKey()+"\t"+entry+"\t"+String.format("0x%04x",word)+"\t"+names+"\t"+context+"\treference-word-candidate-semantics-unverified");
            if(function!=null && score(names)>0) {
                long offset=function.getEntryPoint().getOffset();
                Candidate candidate=candidates.computeIfAbsent(offset,unused -> new Candidate(function));
                candidate.score+=score(names);candidate.names.add(names);
            }
        }
        Files.createDirectories(output);Files.write(output.resolve("traps.tsv"),traps);
        List<Candidate> ranked=new ArrayList<>(candidates.values());
        ranked.sort(Comparator.<Candidate>comparingInt(c -> c.score).reversed().thenComparingLong(c -> c.function.getEntryPoint().getOffset()));
        List<String> notes=new ArrayList<>();notes.add("segment\tfunction_offset\tgenerated_name\tscore\ttrap_reference_names\tdecompile_status\terror");
        DecompInterface decompiler=new DecompInterface();
        try {
            boolean opened=limit>0 && decompiler.openProgram(currentProgram);int attempted=0;
            for(Candidate candidate:ranked) {
                long offset=candidate.function.getEntryPoint().getOffset();String status="not-requested",error="";
                if(opened && attempted<limit) {
                    attempted++;
                    var result=decompiler.decompileFunction(candidate.function,30,monitor);
                    if(result.decompileCompleted() && result.getDecompiledFunction()!=null) {
                        String warning="/* PRIVATE DECOMPILER HYPOTHESIS. Not recovered source or verified gameplay.\n"
                            +" * Segment "+segment+", resource offset "+offset+", SHA256 "+currentProgram.getExecutableSHA256()+".\n"
                            +" * Types, signatures, globals and runtime addresses remain unverified. */\n";
                        String code=result.getDecompiledFunction().getC();
                        Files.writeString(output.resolve("candidate_"+offset+".c"),warning+code);
                        status=code.contains("halt_baddata") || code.contains("Bad instruction") ? "partial-undecoded-hypothesis" : "exported-unverified-hypothesis";
                    } else {status="failed";error=result.getErrorMessage().replace('\t',' ').replace('\n',' ');}
                } else if(limit>0 && !opened) {status="decompiler-open-failed";error=decompiler.getLastMessage().replace('\t',' ').replace('\n',' ');}
                notes.add(segment+"\t"+offset+"\t"+candidate.function.getName()+"\t"+candidate.score+"\t"+String.join(";",candidate.names)+"\t"+status+"\t"+error);
            }
        } finally {decompiler.dispose();}
        Files.write(output.resolve("candidates.tsv"),notes);
        Files.writeString(output.resolve("summary.json"),"{\"segment\":"+segment+",\"known_trap_sites\":"+known+",\"unmapped_trap_sites\":"+unknown+",\"candidate_functions\":"+ranked.size()+",\"runtime_verified\":false}\n");
        println("Segment "+segment+": "+known+" named trap sites, "+unknown+" unmapped, "+ranked.size()+" research candidates");
    }
}
