// Disassemble only validated resource-relative jump targets. All output stays private.
// @category MissionThunderbolt
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.listing.Instruction;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ApplyJumpTable extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=2) throw new IllegalArgumentException("Expected jump-table TSV and private report directory");
        Matcher matcher=Pattern.compile("CODE_([0-9]+)_[0-9]+\\.bin").matcher(currentProgram.getName());
        if(!matcher.matches()) return;
        int segment=Integer.parseInt(matcher.group(1));
        if(segment==0) return;
        Map<Long,String[]> a5=new HashMap<>(); List<String[]> entries=new ArrayList<>();
        List<String> lines=Files.readAllLines(Path.of(args[0]));
        for(int i=1;i<lines.size();++i) {
            String[] row=lines.get(i).split("\t");
            if(row.length!=4) throw new IllegalArgumentException("Malformed jump row");
            a5.put(Long.parseLong(row[3]),row);
            if(Integer.parseInt(row[0])==segment) entries.add(row);
        }
        for(var block:currentProgram.getMemory().getBlocks()) block.setExecute(true);
        int accepted=0;
        for(String[] entry:entries) {
            Address target=toAddr(Long.parseLong(entry[2]));
            if(disassemble(target)) {
                if(getFunctionAt(target)==null) createFunction(target,"jump_"+entry[1]);
                accepted++;
            }
        }
        List<String> edges=new ArrayList<>();
        edges.add("source_segment\tsource_offset\tsource_function_offset\tkind\ttarget_segment\ttarget_offset\tconfidence");
        var instructions=currentProgram.getListing().getInstructions(true);
        int instructionCount=0;
        while(instructions.hasNext()) {
            Instruction instruction=instructions.next();instructionCount++;
            if(!instruction.getFlowType().isCall()) continue;
            var function=getFunctionContaining(instruction.getAddress());
            String sourceFunction=function==null ? "" : Long.toString(function.getEntryPoint().getOffset());
            String source=segment+"\t"+instruction.getAddress().getOffset()+"\t"+sourceFunction+"\t";
            boolean resolved=false;
            for(int operand=0;operand<instruction.getNumOperands();++operand) {
                boolean usesA5=false;Scalar displacement=null;
                for(Object object:instruction.getOpObjects(operand)) {
                    if(object instanceof Register && ((Register)object).getName().equalsIgnoreCase("A5")) usesA5=true;
                    if(object instanceof Scalar) displacement=(Scalar)object;
                }
                if(usesA5 && displacement!=null) {
                    String[] dest=a5.get(displacement.getSignedValue());
                    if(dest!=null) {
                        edges.add(source+"a5-jump-call\t"+dest[0]+"\t"+dest[2]+"\tjump-table-resolved");
                        resolved=true;
                    }
                }
            }
            if(!resolved) {
                Address[] flows=instruction.getFlows();
                if(flows.length==0) edges.add(source+"indirect-call\t\t\tunresolved");
                for(Address flow:flows) {
                    boolean internal=currentProgram.getMemory().contains(flow);
                    edges.add(source+"direct-call\t"+(internal?segment:"")+"\t"+flow.getOffset()+"\t"+(internal?"segment-relative-static":"unresolved-external"));
                }
            }
        }
        Path output=Path.of(args[1]);Files.createDirectories(output);
        Files.write(output.resolve("CODE_"+segment+"_calls.tsv"),edges);
        Files.writeString(output.resolve("CODE_"+segment+"_summary.json"),
            "{\"segment\":"+segment+",\"jump_entries\":"+entries.size()+",\"disassembled_entries\":"+accepted+",\"instructions\":"+instructionCount+",\"call_edges\":"+(edges.size()-1)+",\"runtime_addresses_known\":false,\"game_semantics_verified\":false}\n");
        println("Segment "+segment+": "+accepted+" jump entries, "+instructionCount+" instructions, "+(edges.size()-1)+" static call candidates");
    }
}
