// Exact decoded A5 displacement references, never a raw-byte or alias analysis.
// @category MissionThunderbolt
import ghidra.app.script.GhidraScript;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

public class ExportA5References extends GhidraScript {
    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=2)throw new IllegalArgumentException("Expected comma-separated signed displacements and private output directory");
        Set<Long> offsets=new HashSet<>();
        for(String value:args[0].split(",")) {
            long displacement=Long.decode(value);
            if(displacement<Short.MIN_VALUE || displacement>Short.MAX_VALUE)throw new IllegalArgumentException("Expected signed 16-bit displacements");
            offsets.add(displacement);
        }
        var match=Pattern.compile("CODE_([0-9]+)_[0-9]+\\.bin").matcher(currentProgram.getName());
        if(!match.matches())return;
        int segment=Integer.parseInt(match.group(1));
        Path repo=Path.of(getSourceFile().getAbsolutePath()).toRealPath().getParent().getParent().getParent();
        Path output=Path.of(args[1]).toAbsolutePath().normalize();
        if(output.startsWith(repo) && !output.startsWith(repo.resolve("local-generated")))
            throw new IllegalArgumentException("Keep original-derived references private");
        Files.createDirectories(output);Path report=output.resolve("CODE_"+segment+"_a5.tsv");
        if(Files.exists(report))throw new IllegalArgumentException("Refusing to overwrite references");
        var rows=new ArrayList<String>();
        rows.add("segment\tinstruction_offset\tfunction_offset\tdisplacement\toperand\treference_type\tinstruction\tsource_sha256");
        var instructions=currentProgram.getListing().getInstructions(true);
        while(instructions.hasNext()) {
            var instruction=instructions.next();
            for(int operand=0;operand<instruction.getNumOperands();++operand) {
                boolean a5=false;Scalar scalar=null;int registers=0,scalars=0;
                for(Object object:instruction.getOpObjects(operand)) {
                    if(object instanceof Register) {registers++;a5|=((Register)object).getName().equalsIgnoreCase("A5");}
                    if(object instanceof Scalar) {scalars++;scalar=(Scalar)object;}
                }
                // Reject indexed/ambiguous operands. Aliases through A0 etc. are deliberately absent.
                if(!a5 || registers!=1 || scalars!=1 || !offsets.contains(scalar.getSignedValue()))continue;
                var function=getFunctionContaining(instruction.getAddress());
                rows.add(segment+"\t"+instruction.getAddress().getOffset()+"\t"+
                    (function==null?"":Long.toString(function.getEntryPoint().getOffset()))+"\t"+
                    scalar.getSignedValue()+"\t"+operand+"\t"+instruction.getOperandRefType(operand)+"\t"+
                    instruction.toString().replace('\t',' ')+"\t"+currentProgram.getExecutableSHA256());
            }
        }
        Files.write(report,rows);println("Exported "+(rows.size()-1)+" exact decoded A5 references in CODE "+segment);
    }
}
